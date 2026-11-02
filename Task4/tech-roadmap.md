# Технологическая дорожная карта

Зоны отражают решение для кейса. **Adopt** — использовать в базовом решении после штатного допуска; **Trial** — ограниченный пилот с измеримым gate; **Assess** — исследовать до выбора; **Hold** — не включать в текущую программу. Это не утверждение, что технологии уже закуплены или развернуты.

| Зона | Технология / подход | Горизонт и обоснование | Условие применения / выхода |
|---|---|---|---|
| Adopt | Customer Hub на PostgreSQL, identity/authority workflow | М1–М3: source crosswalk и ограниченный golden profile быстрее полнофункционального MDM; транзакционные ограничения и аудит | Подтверждённые matching rules, stewardship, merge/unmerge и HA; не превращать Hub в финансовый master |
| Adopt | PostgreSQL DWH, Airflow, dbt | М2–М3: обычный SQL/ELT достаточен для MVP, DAG/retry, версии моделей и тесты | Benchmark объёма, extraction budget, isolation ingest/BI, backup/restore; Spark не нужен для простого SQL close |
| Adopt | DataHub, glossary, ownership, lineage | Минимум М3, расширение до М12: отсутствие каталога — текущая проблема | Metadata connectors и manual mapping для legacy; runtime access контролируется отдельно |
| Adopt | FU ESB + адаптеры, versioned contracts, manifests | М1–М3: переиспользовать существующую интеграцию и изолировать модели RB | Поддерживаемые API/export/CDC, checkpoints, quotas; шина не становится DWH |
| Adopt | Object landing/archive и проверяемый PITR | М2–М3 и далее: provenance, повтор загрузки, неизменяемые входные версии | ИБ, encryption/key recovery, retention/legal hold, restore evidence; выбор площадки не задан |
| Trial | Kafka + Schema Registry / Avro | М4–М8: несколько consumers, replay и канал-события требуют устойчивого журнала | Пилот lag, ordering по aggregate, schema evolution и восстановления; размер/retention по измерениям. Для MVP batch остаётся достаточным |
| Trial | Iceberg/Parquet, transactional catalog, Spark, Trino | М4–М8: большие backfills и события, snapshots и SQL по истории | Пилот P03/P04, compaction, catalog restore и стоимость; после gate — промышленная эксплуатация к М12. DataHub не заменяет catalog |
| Trial | Графовая БД / OpenSearch | После М6 только для подтверждённых graph fraud или поиска кейсов | Улучшение на реальном use case против SQL, ACL/PII и freshness; производные индексы, не master. Без benefit в обязательный target не входят |
| Assess | Полный MDM: vendor / собственное развитие registry | М1–М4: workflow, survivorship, lineage, доступность и эксплуатация важнее бренда | Fit-gap, закупки/поддержка/ИБ и TCO; внедрение выбранного решения после пилота, миграция crosswalk/history |
| Assess | MPP DWH вместо/рядом с PostgreSQL | М4–М8 при доказанном пределе | Проверить SQL/partition/index/replica оптимизацию; менять только при недостижении согласованной нагрузки/окна и приемлемом TCO |
| Assess | FU как Target Core/Cards/Loans/CRM | М1–М6: существующая система — кандидат, а не автоматически winner | Coverage продуктов RB, юридические/процессинговые зависимости, миграция истории и capacity; отдельные cohort cutovers |
| Hold | Big-bang replacement RB и dual financial writers | Не соответствует непрерывности и корректности | Только отдельное новое решение с доказательствами могло бы пересмотреть ограничение; в текущем плане исключено |
| Hold | Полный Data Mesh и отдельная платформа каждой команды | До зрелости ownership/контрактов — лишняя стоимость и разрыв контроля | Сейчас пять data-продуктов на общей платформе; дальнейшая децентрализация по измеренному bottleneck |
| Hold | Universal event sourcing / MDM для всех объектов | Не требуется для общей отчётности и ломает operational ownership | Использовать CDC/outbox и профильные OLTP masters; Kafka — транспорт данных, не новая книга учёта |
| Hold | BI/Trino federation в production Core | Нарушает изоляцию OLTP/OLAP | Только асинхронные analytical copies; оперативные product APIs не подменяются аналитическими joins |

На М3 принимается минимальная платформа, на М6 — результаты пилотов/выбора MDM, на М9 — data products и готовность legacy cohorts, на М12 — промышленная приёмка и подтверждённый residual legacy plan. Обновление зоны Trial → Adopt требует владельца эксплуатации, runbooks, ИБ, измерений и аварийной репетиции, а не только успешного demo.
