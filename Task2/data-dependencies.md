# Зависимости и риски данных

| Проблема / зависимость | Последствие | Контроль / решение и владелец |
|---|---|---|
| Разные source IDs и ложный merge | Неверный Customer 360, смешение ролей/доступа | Crosswalk version, verified matching, manual review/unmerge; Party owner |
| Общие имена продуктов при разных тарифах | Неверная сегментация/доходность, изменение договорных условий | Product equivalence matrix с effective dates; Product + Legal |
| Карточное событие и соответствующая проводка Core загружены как две операции | Двойной оборот/доход | Source-fact authority, event→posting linkage; Cards + Finance |
| Локальные business dates, timezones и late postings | Несходящиеся периоды при одном timestamp cutoff | Source close markers, watermark vector, restatement; Finance |
| Межбанковский перевод отражён в двух книгах | Ошибочная «дедупликация» законных записей либо завышенная консолидация | Сохранить обе книги; отдельные утверждённые elimination rules для внутригруппового представления |
| Нет подтверждённого CDC/snapshot/log retention | Gap или потеря незавершённых транзакций при bootstrap | Source-specific POC, snapshot + retained committed changes; DBA/integration |
| Двусторонний sync CRM/Hub | Ping-pong, неконтролируемый last-write-wins | Field authority, origin/version, no echo, conflict workflow; MDM + CRM |
| Расхождение subledger/Loans с Core | Неверная задолженность/регуляторный показатель | Отдельные principal/interest/fees и accounting bridge; Loans + Finance |
| Отзыв согласия не дошёл до BI/search/Lakehouse | Незаконное дальнейшее использование производных копий | Purpose-aware access и acknowledgements, lineage consumer inventory; Privacy |
| Удаление/merge изменили историю измерений | Нельзя повторить уже сданную форму | Bitemporal mapping, SCD2, snapshot and release IDs; Data Office/Finance |
| Аналитика/CDC конкурируют с OLTP | Деградация клиентских сервисов | Нет прямого BI к OLTP; bounded capture/backfill и approved overhead; эксплуатация |
| Каталог показывает путь, но в отчёте другая версия SQL | Формальный lineage не объясняет опубликованные цифры | Run-level input/output snapshots, code hash, mapping version; Data Platform |
| Покупка банка ошибочно трактуется как слияние юрлиц | Потеря book/legal entity и неправильные права обработки | Юридические границы, договорные основания и консолидация подтверждаются отдельно; Legal/Finance |

До production надо уточнить объёмы/скорости/окна закрытия, СУБД и разрешённые API, регуляторные формы/сроки, RPO/RTO, retention/legal hold, штат/budget, поддерживаемые технологии и residency. Эти пробелы влияют на capacity, vendor selection и дату переключения; отсутствующие значения не считаются нулём или разрешением принять произвольный норматив.
