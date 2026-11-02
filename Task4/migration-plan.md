# Инкрементальный план миграции

Восемь этапов на горизонте года. Диапазоны месяцев — план для согласования, а не оценка по известному штату. Работы могут перекрываться, но следующий перенос не обходит критерии выхода. [Дорожная карта PNG](diagrams/migration-roadmap.png), [PlantUML](diagrams/migration-roadmap.puml).

| Этап / горизонт | Содержание и зависимости | Результат и gate | Ответственный |
|---|---|---|---|
| 1. Discovery, М1 | Реестр источников/таблиц/consumers/ПДн, profiling, текущие объёмы и пики, доступные export/CDC, бюджет чтения OLTP, recovery и retention. Доступ к production согласуется штатным процессом | Inventory, Data Owners, source/date history map; подтверждены возможности capture и backup; открытые вопросы имеют owner/date | Data Office + владельцы систем + ИБ |
| 2. Модель и authority, М1–М2 | На основе discovery: E01–E15, BIAN, product/reference mapping, финансовые grain, KYC matching, legal entity/book, SLO и критерии качества | Утверждены field authority и запреты auto-merge, матрица master-owner, словарь показателей, privacy и cutoff policy | Data Office + Finance + CRM/Core owners |
| 3. Hub и адаптеры, М2–М3 | Registry PostgreSQL, crosswalk, stewardship, поддерживаемые CDC/export; snapshot+delta, replay, loop suppression F01–F06; input manifests | Source IDs покрыты enterprise/provisional IDs, спорные записи в очереди; replay без дублей; нет финансовых dual writes | MDM и integration teams |
| 4. MVP отчётности, М2–М3 | После договорённостей этапа 2: отдельный PostgreSQL DWH, P02 Airflow/dbt, четыре marts, минимальный DataHub; F07–F13 | Совместные отчёты по клиентам/счетам/продуктам/операциям сверены; lineage и permissions; срез D+1 06:00 МСК как предлагаемый SLO | DWH team + Finance |
| 5. Shadow и cutover, к концу М3 | Параллельные расчёты общего определения по новым и старым источникам; репетиция fallback, fixed versions; этапы 3–4 завершены | Пройден [cutover](cutover-plan.md); оба BI читают один accepted release. Без gate остаётся контрольная версия и эскалация риска срока | Finance, release manager, operations |
| 6. История и события, М4–М8 | P03/P04: Kafka/Avro для нескольких consumers, Iceberg/Spark/Trino по нагрузочным пилотам; ingest FU Lake с manifest; MDM workflow и HA | Повторы и история сверены, catalog restore и retention проверены; не увеличена нагрузка на Core; нет пересечения финансовых фактов | Data platform + Cards/channel owners |
| 7. Продукты и потребители, М6–М10 | Контракты DP01–DP05, consumer migration, CRM cases/consents; assessment Core/Cards/Loans cohorts; обновление lineage | Владельцы приняли продукты; для каждого переключения отдельный gate; финансовое мастерство переносится только с fencing | Доменные owners + platform |
| 8. Вывод legacy и приёмка, М9–М12 | Завершённые когорты/consumers; archive/restore rehearsal, удаление старых маршрутов, обучение и support handover | Выполнены [критерии цели](migration-target-state.md); RB остатки имеют owner/стоимость/следующий milestone, отсутствуют бесхозные flows | Steering committee + business owners |

## Как сократить риск срока в три месяца

В MVP входят registry/matching, authority matrix, четыре SQL marts, критичные DQ и минимальный каталог. Kafka, Spark, полная миграция АБС, графовая БД и поисковый индекс не являются предшественниками общей отчётности. При недостатке capacity сначала сокращается число некритичных атрибутов и дополнительных витрин; финансовая сверка, privacy и учёт unresolved clients не сокращаются.

На контрольной точке конца М1 подтверждаются зависимости от поставщиков, операционные окна, доступность выгрузок и capacity платформы. Если capture/проверяемый source close недоступен, выбирают поддерживаемый закрытый batch export и пересогласовывают свежесть. Нельзя объявлять near-real-time при получении файла раз в сутки.

## Единица миграции и доказательства

Единица — именованный набор `(source, legal_entity, book, product/cohort, business_date range, consumer)`. Для него сохраняются manifest с количеством и hash, схема, source cutoffs, code/config hash, mapping/FX versions, DQ, reconciliation, approvals, route before/after и rollback evidence. History ownership map исключает повторный импорт одинаковых проводок из Core, старого DWH и Lakehouse.

Перевод read consumer и передача write ownership — разные изменения. При финансовой миграции source fence запрещает новые команды для принятой когорты, durable routing отправляет их единственному владельцу, in-flight операции завершаются/разрешаются до смены owner epoch. Способ непрерывного обслуживания и возврата после новых записей проектируется и репетируется отдельно: откат DNS или восстановление старого backup не возвращает новые платежи корректно. Текущий [cutover](cutover-plan.md) переключает только отчётность.
