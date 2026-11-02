# Риски миграции

Вероятности ниже — качественная проектная оценка по фрагментированному ландшафту кейса, а не статистика инцидентов банка. После discovery owners пересматривают оценки и residual risk; финансовые/правовые hard gates не снимаются из-за срока.

| Риск | Влияние | Вероятность | Митигация и сигнал | Владелец |
|---|---|---|---|---|
| Ложное объединение клиентов | Чужие данные, неверная аналитика/доступ | Высокая | KYC/evidence и field authority, запрет phone-only merge, steward review, reversible mapping; контроль спорных совпадений. Merge не меняет authorization | CRM owner / Data Office |
| Пропуск CDC или длинной транзакции | Неполные финансовые факты | Средняя | Snapshot+retained changes, committed boundary, checkpoints, retention alarm; сверка close totals; при gap остановить release и bootstrap | Integration / source DBA |
| Двойной writer при переносе | Двойное списание, конфликт балансов | Средняя | Ownership registry/epoch/fencing, отдельный cutover финансовой когорты, запрет active-active на один объект | Core owner |
| Тройная загрузка из Core, старого DWH и Lakehouse | Завышенные обороты | Высокая | Source/date ownership manifests, unique source keys, раздельные event/ledger grains; отчёт по overlap | DWH / Finance |
| M:N customer join или смешение валют | Завышение показателей | Высокая | Grain tests, контроль до bridge, versioned FX, totals по валюте/книге; запрет sum всех posting legs как payment volume | Finance / analytics |
| Разные cutoff/метрики банков | «Сходящиеся» неверные отчёты | Высокая | Единый словарь, вектор cutoffs, fixed versions и shadow reconciliation; late facts — новый release | Finance |
| Нагрузка extraction на OLTP | Деградация обслуживания | Средняя | Поддерживаемый CDC/export, quotas и окна, мониторинг source CPU/IO/locks; остановить extraction, сохранить customer service | Source owners |
| Потеря consent/retention/ИБ-контроля | Несанкционированная обработка | Средняя | Purpose-aware controls, masks, audit, approvals Legal; restrictions до всех derived stores включая snapshots/backup restore | ИБ / Legal |
| Нет рабочего fallback | Длительный сбой общей отчётности | Средняя | Принятый consolidated bundle того же cutoff, replay/restore rehearsal, inventory consumers; запрет GO без проверки | Operations / Finance |
| Drift схемы/маршрута/SQL | Разные показатели между BI и утрата lineage | Высокая | Versioned contracts/config, freeze, pinned release, consumer probes, dbt/DataHub run evidence | Integration / BI |
| Слишком раннее отключение legacy | Потеря истории/скрытого consumer | Средняя | Usage inventory, период наблюдения, архив и restore, снятие маршрутов по gate, owner sign-off | Legacy owner |
| Недостаток команд/поддержки поставщиков | Срыв трёхмесячного MVP | Высокая | Capacity/vendor commitment в М1, ограниченный MVP, Kafka/Lakehouse после пилота, еженедельная проверка критических зависимостей | Programme owner |
| Kafka lag/retention или сбой catalog | Невозможность replay/чтения истории | Средняя | Проверка failure domains, retained raw manifests, restore Iceberg catalog+objects, replay drills и lag alerts | Data platform |
| Неполная идентификация скрыта в KPI | Ложное число уникальных клиентов | Высокая | Явные provisional/unresolved категории, completeness denominator, подписанный порог и маркировка отчёта | Data Office / Finance |

Отклонения ведутся с incident/change ID, scope, owner, сроком и доказательством закрытия. Материальный финансовый дефект, раскрытие данных или потеря source completeness переводят соответствующий release в NO-GO; независимые неповреждённые процессы продолжают работать.
