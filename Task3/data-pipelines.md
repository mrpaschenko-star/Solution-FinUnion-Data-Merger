# Пайплайны и большие данные

Все pipelines сохраняют source scope/positions, run ID, schema/mapping version, quality results и output release/snapshot. Повтор run не создаёт вторую денежную операцию: это аналитическая загрузка, а не команда в АБС.

| ID / пайплайн | Источник | Приёмник | Тип | Инструменты и обоснование |
|---|---|---|---|---|
| P01 Клиентская идентификация | FU/RB CRM + разрешённые KYC/Party fragments Core | Hub/MDM → consumers/dimensions | Incremental ETL, matching/stewardship | ESB adapters, PostgreSQL Hub, workflow; SQL для правил, fuzzy matching только после размеченного POC |
| P02 MVP financial close | Закрытые source exports Core/Cards/Loans + snapshot Hub/reference | PostgreSQL DWH, четыре management marts | Простой batch ELT | Airflow orchestration, typed CSV/Parquet + manifest, PostgreSQL COPY/staging, dbt SQL/tests; без обязательного Spark/Kafka в MVP |
| P03 История карт | FU/RB Cards, архивные DWH exports в непересекающемся scope | Iceberg → approved aggregates/DWH | Batch backfill + subsequent increments | Object manifests, Spark transforms, Iceberg snapshots; source→posting correlation |
| P04 События каналов | Поддерживаемые канальные producers, разрешённые identity refs | Kafka → Iceberg events → риск/аналитика | Streaming + event-time windows | Kafka/Schema Registry, streaming workers/Spark, dedup/checkpoints; Airflow только deployment/backfill orchestration |
| P05 Справочники/продукты/FX | Domain owners, approved Treasury feed | MDM → DWH/Lakehouse dimensions | Versioned ETL/batch | Workflow approval, SQL validations, dbt SCD2; source rates и правила не выдумываются |
| P06 Регуляторная отчётность | Certified DWH release + согласованные control registers | Закрытый export package → Finance → внешний получатель | Batch, approval, audit | Airflow, dbt/SQL, форматы конкретной формы, signatures/checksums. Эксплуатация не подаёт форму без Finance approval |

## P02 — простой PostgreSQL DWH за три месяца

1. Источники завершают свой business day и выдают read-only export с manifest: legal entity/book/day, schema, rows/counts, debit/credit totals по валюте, позиции/диапазоны, checksum и closure flag. Извлечение из разрешённой реплики/export API, не тяжёлый join по live OLTP.
2. Airflow проверяет наличие всех ожидаемых manifests. Missing source/незакрытый день блокирует certified release; можно показать draft с явной неполнотой, но не заменить им утверждённый отчёт.
3. PostgreSQL `COPY` загружает CSV либо подготовленный binary COPY stream в staging выбранного run. Parquet предварительно читает адаптер, проверяет schema/decimal и преобразует в этот поток: штатный `COPY` не читает Parquet напрямую. Уникальные ключи `(source, legal_entity, book, local_entry_id, version)` и manifest ID делают rerun идемпотентным. Контроль файла защищает transport integrity, но не доказывает полноту финансового дня.
4. dbt нормализует точные decimal, валюты, статусы, source/legal entity keys; join crosswalk/reference использует зафиксированные версии. Unknown/unresolved identity не теряет саму проводку: сохраняется source customer reference/unknown dimension и quality flag. Клиентские агрегаты с неразрешённым matching маркируются отдельно.
5. Строятся `mart_customer_overview`, `mart_account_position`, `mart_product_portfolio`, `mart_postings_daily`. Минимальный scope включает оба банка, выбранный подтверждённый набор счетов/продуктов и операций; исключения явно перечислены, не называются «всем банком».
6. Hard gates: complete manifests, unique entry keys, debit/credit по книге/валюте, opening+movements=closing с принятой sign convention, согласованные source totals/FX/product mappings. Предлагаемый допуск для исходных проводок — **нулевое необъяснённое расхождение**; валютные округления — только по утверждённой политике и отдельной строке контроля.
7. Maker/checker Finance утверждает run; SQL-транзакция переключает `published_release` на набор уже подготовленных таблиц/партиций. Старый release остаётся доступен; BI видит один release ID. Lineage/code/input manifests привязаны до публикации.

Периодичность — daily close с предложенной готовностью D+1 06:00 MSK; intraday — предварительное обновление без подмены закрытой версии. Late correction запускает идемпотентный restatement affected scope и новую версию; backfill не перезаписывает submitted figures. Airflow retries не означают повтор extract всего банка при каждой ошибке: возобновление от проверенного manifest/checkpoint.

## Сценарий больших исторических данных

| Поле | История карточных операций после слияния |
|---|---|
| Источник | FU/RB Cards, старые DWH и архивы; source/date coverage manifest исключает пересечение источников |
| Характер | Большая историческая структурированная/полуструктурированная история authorisation, clearing, settlement и reversals; объём не задан |
| Целевое хранилище | Зашифрованный raw archive → Iceberg curated; approved aggregates в DWH |
| Способ обработки | Partitioned batch backfill, Spark ETL, incremental refresh; key/version dedup и source-to-Core linkage |
| Потребители | Риск-менеджмент, карточная аналитика, расследования; Finance использует лишь сверенные accounting aggregates |

Авторизация не равна списанию; комиссия/возврат/settlement не удаляются как «дубликат». Сверка по дню/юрлицу/валюте/типу события, mapping posted entry reference. Customer crosswalk фиксируется as-of; повторное сопоставление создаёт новую аналитическую версию. Batch quotas не мешают дневному закрытию.

## Сценарий больших событийных данных

| Поле | События мобильного/веб-канала |
|---|---|
| Источник | Instrumented producers двух банков через Integration; канал и legal/purpose scope сохранены |
| Характер | Event stream, разные schema versions, late/out-of-order/duplicate events; не ledger |
| Целевое хранилище | Kafka retention для replay → Iceberg event tables/curated features |
| Способ обработки | Streaming ingest, event ID dedup, event-time windows с согласованным lateness; batch correction/backfill |
| Потребители | Customer experience BI, риск/антифрод исследование и feature preparation; online fraud decision при необходимости — отдельный low-latency serving contract |

Watermark/lateness рассчитывается из профиля событий и согласуется; слишком поздние events не исчезают, а идут в correction path. Event ID уникален в namespace producer; ingestion timestamp не заменяет фактическое время. Consent/purpose и minimization применяются до выдачи features. Lakehouse/Trino не обещает подходящую latency для авторизации банковской операции.
