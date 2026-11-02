# Разделение DWH и Lakehouse

| Критерий | PostgreSQL DWH | Iceberg Lakehouse |
|---|---|---|
| Главный сценарий | Закрытые финансовые периоды, согласованные показатели и regulatory extracts | Большая история, streaming events, exploratory/risk workloads |
| Модель и хранение | Conformed stars, SQL constraints, partitioning и release manifests | Parquet/object storage, Iceberg snapshots/metadata, schema/partition evolution |
| Изменения | Транзакционный stage→publish, версии отчётных наборов | Atomic table commits, MERGE/delete при поддержке движка; multi-table consistency задаётся release manifest |
| Масштаб | Writer/IO/BI contention измеряются, тяжёлые scans выносятся | Compute/storage раздельны; small files/metadata/compaction требуют эксплуатации |
| Governance | Grants, RLS/views, model tests, подписанные releases | Catalog+object ACL, engine policies, row/column security там, где поддержана; прямой bucket доступ закрыт |
| Роль во времени | MVP на 3 месяца; certified контур на 12 месяцев с capacity gate | POC истории, затем production для выбранных больших потоков |

## Какие данные где остаются

**В OLTP:** действующие счета, команды исполнения, договорные условия, графики, учётные транзакции. **В MDM:** golden party/crosswalk/reference decisions. **В DWH:** approved dimensions, posted entries/account daily snapshots, quality/control totals, отчётные версии и целевые показатели. **В Lakehouse:** разрешённые raw/delta copies, исторические карточные события, channel events, нормализованная крупная история и расчётные datasets. **В объектах вне табличного слоя:** договорные документы, export manifests и закрытые архивные пакеты.

Lakehouse не хранит CVV/PIN и не получает полный PAN для удобства аналитики. Bronze ограничен сроком/целями; «raw навсегда» не является политикой банка. Ссылки на клиента псевдонимизируются для соответствующих consumers, mapping доступен отдельно по правам.

## Роль Iceberg и Trino

Iceberg — **формат таблиц и metadata protocol**, не исполняющий SQL сервер. Он обеспечивает snapshots, schema evolution и partition evolution, но требует согласованного writer/catalog и поддерживаемых операций движка. Spark выполняет большие transforms и backfill; Trino читает и при поддержке конкретной версии выполняет нужные DML. Версии Spark/Trino/Iceberg/catalog фиксируются после compatibility POC.

DataHub показывает, откуда данные и кто отвечает; Iceberg REST-compatible catalog управляет table identifiers/commit metadata. Один не подменяет другой. Trino может читать DWH/read replicas для аналитического объединения в пределах quotas; federation на live Core запрещена, иначе исчезнет изоляция OLTP/OLAP.

Iceberg snapshot ID фиксирует версию одной таблицы. Отчёт с несколькими таблицами хранит **вектор snapshot IDs**, mapping/FX/code versions и единый утверждённый cutoff; нельзя считать один случайный snapshot ID distributed transaction всей платформы. После срока snapshot expiration воспроизводимость требует архивного approved release или сохранённых входов и кода.

## Ограничения и контроль

Small files уплотняются compaction jobs с ограничением writer concurrency; partitioning выбирается по дате/крупным сегментам запроса, а не по каждому клиенту. Ошибочный partition key/retention может сделать чтение и удаление дорогими. Delete из текущего snapshot не стирает старые snapshots/backups: purge/legal hold процессы координируются с ИБ/Legal.

PostgreSQL partitioning/read replicas — первые меры, но не обещание бесконечной мощности. При нарушении close window после оптимизации измеряются альтернативы MPP; тогда меняется технический движок с сохранением contract/grain/release semantics. Двойное сопровождение DWH+Lakehouse оправдано только для выбранных workloads и учитывается в resource plan.
