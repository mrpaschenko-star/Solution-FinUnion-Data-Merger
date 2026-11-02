# Потоки переходного состояния

В задании одновременно запрошены «уровень 0» и схема со многими системами/внутренними операциями. Поэтому даны две согласованные схемы: [настоящий context DFD с одним процессом](diagrams/context-zero.png) ([исходник](diagrams/context-zero.puml)) и [развёрнутый ландшафт трёх месяцев](diagrams/flows-3m.png) ([исходник](diagrams/flows-3m.puml)). Последний — обзор границ систем, не строгая декомпозиция каждого процесса до таблиц.

## Каталог потоков

| ID | Источник → приёмник | Сущности и действие | Режим | Назначение |
|---|---|---|---|---|
| F01 | FU/RB CRM → Integration Layer | E01/E11/E13/E14: Create/Update, Validate; approved Delete marker | CDC либо поддерживаемый incremental export, async | Полные source keys, изменения клиента/кейса/согласия без тяжёлых cross-bank запросов |
| F02 | FU/RB Core → Integration Layer | E03/E06/E07/E08/E09/E14: Read/Validate committed facts | CDC с transaction boundaries либо закрытый batch export | Счета, платежи и учётные факты; никаких команд исполнения в этом канале |
| F03 | FU/RB Cards → Integration Layer | E04, связанные authorization/clearing events: Read/Validate | Incremental batch на 3 месяца; streaming по мере готовности | Карточный профиль и lifecycle; mapping с Core postings предотвращает двойной денежный факт |
| F04 | FU/RB Loans → Integration Layer | E05/E06/E14: Read/Validate | Incremental batch/CDC по поддержке | Кредитный портфель и графики с отдельной сверкой учётного остатка |
| F05 | Integration Layer → Customer Hub | E01/E02/E10/E12: Validate/Enrich/Create/Update | Async durable adapter queue/inbox | Normalize/match, golden record, общие product/reference mappings |
| F06 | Hub → Integration Layer → FU/RB CRM и разрешённые Core/Cards/Loans consumers | E02 и разрешённые E01/E10/E12: Update/Enrich | Async с version/origin; read API для lookup | Распространить enterprise ID/справочники, не перезаписывая финансовые owners |
| F07 | Integration Layer → PostgreSQL DWH staging | E03–E11/E14/E15: Read/Create/Validate | Bounded batch; CDC landing где доступно | Изолированная staging/raw копия и manifest для аналитики; затем Aggregate в сертифицированные marts |
| F08 | Hub → DWH | Golden dimensions, crosswalk, product/reference versions: Read/Enrich | Incremental batch + фиксированный snapshot для close | Конформные измерения и воспроизводимая версия идентичности |
| F09 | FU DWH/RB DWH, частичный FU Lake → Integration Layer → DWH/archive | История и контрольные totals: Read/Validate | Batch, manifest | Сравнение со старыми отчётами и явно ограниченная backfill-история; не второй импорт текущих source facts |
| F10 | DWH → FU BI/RB BI / общий semantic dataset | Read/Aggregate: клиент, счета, продукты, posted movements | Published views/версия dataset, sync read в OLAP | Оба BI могут временно жить, но общий показатель берут из одного certified release |
| F11 | Integration/Hub/DWH/BI pipelines → DataHub | Метаданные: Create/Update lineage, quality, owners | События job/run + scheduled harvest | Technical lineage и business glossary; никакой bulk-копии клиентских payload в каталог |
| F12 | Authoritative privacy/domain owner → Integration → Hub/DWH/BI/derived indexes | E01/E11/E13: approved Delete/restrict/anonymize marker | Async с policy/evidence, acknowledgements | Применить разрешённое ограничение/удаление производных данных с учётом financial retention/legal hold |
| F13 | Сертифицированный DWH/report export → регуляторный процесс / регулятор | Read/Validate/Aggregate → утверждённый файл | Закрытие периода, batch и approval | Единая воспроизводимая отчётная база; внешний submission только после Finance approval |

F01–F04 и F07 используют существующий FU ESB и thin adapters RB; actual middleware/DB capability подтверждается discovery. Kafka вводится поэтапно для повторяемого потока, а не объявляется уже работающей за три месяца. Старые point-to-point финансовые команды сохраняются до отдельного перевода владельца; таблица описывает новые data flows.

## Bootstrap, повторы и обратный поток

Для каждого источника получают consistent snapshot на watermark и удерживают изменения до начала snapshot. Позиции логов, незавершённые транзакции и retention проверяются под реальную СУБД: нельзя универсально подставить Oracle SCN или PostgreSQL LSN. Применяют snapshot и committed changes после границы, checkpoint продвигают после durable commit. Повторы dedup по source transaction/change ID; повторы batch по `(source, manifest, row key, version)`.

Вектор source watermarks фиксируется отдельно по источникам; единый timestamp не означает распределённый consistent snapshot. Для финансового дня Finance задаёт closed periods, completeness и cutoff, по которым можно совместно агрегировать книги. Запаздывающие corrections создают restatement новой версии отчёта.

Hub publish содержит `origin`, `master_version`, `correlation_id` и changed attributes. Consumer не превращает полученный master update в новое конкурирующее решение; echo подавляется, конфликт источников рассматривается steward. Счета/проводки по F06 не реплицируются как writable master records. Для непринятого сообщения сохраняются причина и replay position, а не silent drop.

Физический `Delete` в CRM и аннулирование учётной операции — разные события. Posted transaction корректируется reversal; consent revoke ограничивает обработку по цели; удаление производного индекса не удаляет обязательный регистр. Тип действия на DFD относится к соответствующей сущности и её policy.
