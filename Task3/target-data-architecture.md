# Архитектура данных через 12 месяцев

Целевая архитектура разделяет операционные владельцы, сбор/распространение данных, аналитическое хранение и governance. [Диаграмма PNG](diagrams/target-12m.png), [PlantUML](diagrams/target-12m.puml). Она показывает функциональные компоненты, а не утверждённое количество серверов или доступный бюджет.

## Компоненты и ответственность

| Компонент | Роль и решение | Почему / предел |
|---|---|---|
| Operational Systems | Target CRM/Core/Cards/Loans, остаточные RB-системы по ownership registry | Финансовые транзакции локальны у active owner. Кандидаты FU требуют функциональной/нагрузочной проверки, полного одномоментного replacement нет |
| MDM | Party golden records/crosswalk, утверждённые product/reference атрибуты, workflow качества | Защита от ложных merges; финансовый ledger/долг не перемещается в MDM |
| Integration Layer | FU ESB, source adapters, sync lookup APIs, capture/outbox, schema validation, routing | Сохраняет совместимость legacy и контролирует происхождение. Не выполняет BI joins в АБС |
| Kafka + Schema Registry | Partitioned durable stream изменений/событий, Avro, compatibility, replay, consumer groups | Много downstream consumers и массовые backfills; partition key сохраняет порядок конкретного aggregate, не всех счетов мира |
| Landing / object store | Immutable source manifests, raw capture и разрешённые документы | Повторяемая загрузка и доказательство происхождения; шифрование, quotas, retention/legal hold |
| PostgreSQL DWH | Conformed dimensions, financial facts, контрольные totals, certified releases | Воспроизводимая отчётность и SQL; workload isolation/read replicas. При доказанном пределе возможен отдельно выбранный MPP |
| Iceberg Lakehouse | Bronze/silver/curated таблицы большой истории и событий на Parquet/S3 | Table snapshots, schema/partition evolution и изоляция batch readers; не банковский OLTP |
| Iceberg catalog | Поддерживаемый transactional/REST-compatible catalog таблиц и commits | Нужен для согласованных table pointers. **DataHub не заменяет** catalog transaction mechanism Iceberg |
| Spark / Trino | Spark — тяжёлые batch/stream transforms, Trino — SQL по Lakehouse | Spark не нужен для маленького MVP SQL; Trino не направляет federation queries в operational Core |
| Airflow + dbt | Airflow — DAG/schedule/retry/backfill; dbt — versioned SQL models/tests/lineage | Airflow не является брокером и не запускает task на каждую транзакцию; streaming исполняется отдельными workers/jobs |
| BI / semantic layer | Общие определения, published dataset/release ID, row/column controls | Несогласованная metric definition не лечится одной общей БД; Finance утверждает показатели |
| DataHub | Каталог, glossary, ownership, classifications, quality, lineage | Table/column mapping + run evidence; доступ применяется в runtime, а не только помечается тегом |

Технологии — кандидаты для внедрения с проверкой поддерживаемых версий, эксплуатации, закупок и ИБ. Ни on-prem, ни конкретное облако не заданы кейсом; данные размещаются в согласованной юрисдикции/площадке. Существующий ESB не выбрасывается ради Kafka: командные integrations и data streaming выполняют разные функции.

## Основные пути

Source commit → ограниченный CDC/export → validation/landing → MDM или аналитический pipeline. MDM публикует versioned identity/reference decisions обратно через Integration и в аналитические dimensions. Kafka переносит события и source references, а не означает, что каждое событие должно быть executable payment command.

Текущие закрытые финансовые факты поступают в DWH из подтверждённого operational landing. Большая историческая/канальная информация обрабатывается в Iceberg; согласованные aggregates/исторические facts переходят в DWH по отдельному manifest и **непересекающемуся source/date scope**. Один логический posting не загружается одновременно из raw Core, старого DWH и Lakehouse как три факта.

DWH публикует BI и регуляторный export после hard gates. Trino даёт исследовательский доступ к разрешённым Lakehouse datasets; регуляторный отчёт не строится ad hoc на меняющейся bronze-таблице. Старый FU Data Lake инвентаризируется, нужные datasets конвертируются/регистрируются, а не объявляются Iceberg после простого переименования bucket.

## Надёжность, безопасность и управление

Producer outbox/capture position и consumer inbox/checkpoint обеспечивают восстановимые повторы. В Kafka предлагаются replication factor 3, `acks=all`, `min.insync.replicas=2` при трёх независимых failure domains; это проектная topology, требует ресурсов и проверки отказа. Транзакции Kafka не обеспечивают автоматически exactly-once запись в произвольную БД. Retention определяется допустимым outage/replay и объёмами; если диапазон удалён, нужен согласованный snapshot bootstrap.

MDM/DWH — HA writer с fencing, проверяемые backup/PITR, отдельные роли/schema и quotas для ingest/BI. Lakehouse имеет защищённый object storage и catalog backup, version retention и процедуры исправления неудачной публикации. Реплика не backup; восстановление store, keys, metadata и permissions проверяется совместно. RPO/RTO и требуемые failure domains — обязательные открытые решения владельцев, до них нельзя обещать время recovery.

DataHub получает schema versions, dbt manifests/tests, Airflow run IDs, source/output snapshots и сопоставление поля отчёта с transforms. Если автоматический column lineage не поддержан для legacy SQL/процедуры, mapping вносится вручную и подтверждается owner. Release хранит input manifest, code/config hash, customer mapping version, FX/product versions и approvals.

Несовместимая schema останавливает затронутый consumer, сохраняет raw input и incident; изменение financial meaning требует новой contract version. Quarantine не скрывается в denominator качества. Privacy restrictions проходят lineage-derived список consumers; Iceberg snapshot/time travel и immutable archive тоже учитываются при erase/legal hold policy.
