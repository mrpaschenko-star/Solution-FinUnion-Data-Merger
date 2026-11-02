# Cutover объединённой управленческой отчётности

Переключаем F10 и общий опубликованный dataset на PostgreSQL DWH. В scope четыре [MVP marts](../Task3/data-pipelines.md), согласованные юрлица/книги/продукты и отчётный день. Core, Cards и Loans продолжают операции и сохраняют мастерство; регуляторный submission F13 требует отдельного approval по форме. [Sequence PNG](diagrams/reporting-cutover.png), [PlantUML](diagrams/reporting-cutover.puml).

## Ответственность и условия GO

Release manager ведёт журнал переключения. DWH owner готовит release, Finance maker выполняет бизнес-сверку, независимый Finance checker принимает её. Operations владеет маршрутом и fallback, ИБ — доступом. Решение GO совместно принимают Finance и release manager после всех обязательных approvals; любой hard-gate failure означает NO-GO.

До репетиции должны быть заполнены следующие параметры. Их отсутствие блокирует GO, но не проектирование и реализацию MVP.

| Параметр | Кто определяет | Что нужно зафиксировать |
|---|---|---|
| Cutoff и состав | Finance + owners источников | Юрлица/книги/даты, source close markers, правила поздних commit и коррекций |
| Качество и округление | Finance + Data Office | Ноль необъяснённых денежных расхождений; допустимое FX rounding только по явному правилу; пороги unresolved identities и обязательных атрибутов |
| Recovery | Operations + Finance | RPO/RTO публикации/MDM/DWH, допустимая устарелость отчёта, срок fallback и срок сохранения rollback assets |
| Наблюдение | Finance + Operations | Число успешных закрытий в shadow, длительность усиленного мониторинга и события, требующие rollback |
| Технические маршруты | BI/DWH owners | Точные datasets/views/endpoints, consumers и subscriptions, версии config, способ атомарной смены release и очистки кешей |
| Capacity и ресурсы | DBA + source owners | Объём/длительность final delta, нагрузочный бюджет extraction, доступные исполнители и дежурства |

## Пошаговый runbook

| Шаг | Действие | Проверяемый результат / остановка |
|---|---|---|
| 1. Подготовка | Завершить shadow на общей методике, проверить contracts/DQ/lineage, закрыть критические расхождения. Создать backup/PITR restore point DWH/Hub и сохранить routing/config. Выполнить восстановление на изолированном стенде | Есть протокол восстановления, доступ checker, реестр consumers и подписанные acceptance criteria. Backup без restore-проверки не является gate |
| 2. Подготовка fallback | На старых FU/RB DWH получить согласованный consolidated control bundle **на тот же cutoff и по тем же определениям**. Зафиксировать источник каждого раздела, approved mappings и release ID. Сохранить предыдущий accepted release | Finance принимает fallback заранее. Два старых несопоставимых dashboard не считаются заменой общей отчётности |
| 3. Data freeze | Зафиксировать версии отчётных SQL/метрик, schema mapping, FX, product/reference, Hub crosswalk snapshot и конфигурацию publication. Новые master updates продолжают поступать, но не меняют pinned snapshots | OLTP записи и обслуживание клиентов не останавливаются. Изменение замороженного артефакта требует нового candidate release и повторной сверки |
| 4. Финальная выгрузка | Получить source close markers и **вектор позиций**; довести snapshot/committed delta до согласованной границы, выгрузить final manifests/контрольные totals. Отдельно разрешить long-running и late transactions | Доказана полнота каждого источника. Более поздние commit идут в следующий release/restatement; календарное время само по себе не доказывает полноту |
| 5. Загрузка | Записать staging под новым run ID, проверить hashes/row counts, дедуп по source key/version. Выполнить P02, as-of joins с pinned dimensions, сформировать четыре marts в candidate release | Retry не добавляет повторные факты. Consumer checkpoints продвигаются после durable commit; опубликованный release не изменён |
| 6. Сверка | Выполнить технические и бизнес-контроли ниже. Finance maker сверяет, checker подписывает результаты | Все hard gates пройдены. Карантин денежных фактов без объяснения блокирует GO; не исключать ошибки из знаменателя качества |
| 7. Переключение | DWH транзакционно меняет `published_release_id`. BI получает новый manifest/dataset version; requests pin release ID. Переключить зарегистрированные consumers, invalidate caches/exports и проверить контрольные запросы | Нельзя смешать marts двух releases в одном отчёте. Между двумя BI нет распределённой атомарности: общий manifest — источник версии, неготовый consumer остаётся на явно обозначенной старой версии |
| 8. Наблюдение | Усиленный мониторинг свежести, reconciliation, DQ, latency BI, ошибок доступа, source нагрузок, release IDs и cache hit на старую версию | Finance принимает первое закрытие и последующие в согласованном окне. Старые потоки не отключаются до отдельного gate |

## Контроли перед публикацией

Технические: manifest hash/размер/row count, schema compatibility, уникальность фактов, полнота source/date scope, referential integrity, непересекающиеся SCD2 intervals, source watermark lag, доступность lineage и approvals.

Финансовые: суммы и количество по источнику/юрлицу/книге/дате/валюте; debit/credit balancing в принятой модели; начальный остаток + движения = конечный остаток; totals с source close и независимым control bundle; reversals и FX versions; отдельный контроль intragroup eliminations. Сумма всех ног проводки не объявляется объёмом платежей. Дубликаты карточных events/ledger и размножение сумм при customer bridge joins исключаются тестами.

Клиентские: доля unresolved/provisional IDs, подтверждённость merge, полнота обязательных атрибутов и orphan contracts. Неоднозначные совпадения не объединяются ради красивого количества клиентов. Отчёт явно показывает покрытие идентификации; порог Finance/Data Office согласуется до GO.

Контрольные суммы файлов доказывают доставку байтов, но не верность финансовой семантики. Даже совпавшие общие итоги не заменяют контроль по книге, валюте и источнику.

## Fallback после GO

Триггеры: необъяснённое денежное расхождение, неверные права/раскрытие данных, смешение releases, недоступность или свежесть за согласованным порогом. Operations останавливает новые публикации/подписки затронутого scope; сохраняет input, logs и candidate evidence. При утечке немедленно ограничивает доступ и запускает incident response.

1. Finance и release manager выбирают заранее принятый control bundle на тот же cutoff. Если он недоступен/устарел, разрешён только последний принятый release с **видимой датой и ограничением применимости**; это состояние деградации и инцидент, а не успешный текущий отчёт.
2. Operations возвращает pointer/dataset routing/config на выбранную версию. BI owners проверяют оба BI, кеши, выгрузки, расписания и права; контрольный запрос обязан вернуть её release ID и totals.
3. Уже выпущенные ошибочные файлы помечаются отозванными, зарегистрированные recipients получают исправление штатным процессом. Отчёты и approvals сохраняются для аудита. Регуляторная пересдача решается Finance отдельно.
4. DWH team исправляет причину, повторяет загрузку идемпотентно под **новым** release ID, сверку и maker/checker. Возврат на новую платформу — повторное GO, без молчаливой подмены старой версии.

Rollback не восстанавливает production Core из backup и не отменяет банковские транзакции. Репетиция проверяет время смены publication и восстановления данных против согласованных RTO/RPO; если оно не достигнуто, fallback считается неготовым.
