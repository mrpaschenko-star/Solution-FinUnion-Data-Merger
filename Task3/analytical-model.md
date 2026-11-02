# Аналитическая модель финансовых движений

Выбрана **звезда**: конформные измерения и заранее определённый grain упрощают SQL, lineage и проверку агрегатов. Снежинка увеличила бы число joins для сравнительно стабильных product/branch attributes, поэтому нормализация справочников остаётся в MDM, а DWH предоставляет денормализованные dimension versions. [Диаграмма PNG](diagrams/analytical-star.png), [PlantUML](diagrams/analytical-star.puml).

| Тип / таблица | Grain и ключи | Меры / атрибуты |
|---|---|---|
| Fact `fact_ledger_entry` | **Одна posted проводка исходного ledger**; уникален source_system + legal_entity/book + source_entry_id + source_version | amount в валюте записи, debit_credit, signed amount по утверждённому account-type rule; source_transaction_id/payment_id как degenerate dimensions, reversal_ref, release_id |
| Fact `fact_account_daily` | Один счёт × business_date × currency × book × accepted release | opening/closing balance, debit/credit turnover раздельно; semi-additive по времени — остатки разных дней не суммируются |
| `dim_account` | SCD2 версия счёта | Account type, status, source key, book, effective interval; не секреты доступа |
| `dim_product` | SCD2 версия продукта/тарифа | Unified product class, source mappings, действовавшие условия |
| `dim_customer` | Версия разрешённого golden профиля | Enterprise ID, type/segment, quality/provisional status; минимум ПДн |
| `bridge_account_party` | Счёт × клиент × роль × effective interval × mapping_version | Связь через договор/сторону, evidence; доли только если бизнес утвердил allocation policy |
| `dim_legal_entity` | Юрлицо/книга | Раздельный учёт и консолидационная группа |
| `dim_currency` | Валюта/версия справочника | Код/precision; валюты нельзя суммировать без conversion |
| `dim_date` | Календарная/банковская дата | Business calendar, период, fiscal attributes |
| `dim_fx_rate` | Rate date/type/provider/currency pair/version | Утверждённый rate; если используется reporting amount, fact ссылается на конкретный rate key |

## Правила агрегации

E07 имеет несколько E08: сумма абсолютных значений всех ног не равна объёму платежей. По `fact_ledger_entry` считаются debit/credit turnover и контрольные итоги **счёта/книги**. Для числа/объёма платежей нужен отдельный согласованный grain `(executed payment, execution part)`, либо отбор определённых posted legs с доказанным mapping; `SUM(amount)` всех проводок в качестве «объёма переводов» запрещён.

Карточные authorisation/clearing events находятся в Lakehouse/Card Activity; `fact_ledger_entry` получает ledger из Core как финансовый источник. Данные старого DWH загружаются только для непокрытого source/date scope после контроля ключей. Внутригрупповые операции сохраняют обе стороны в разных книгах; консолидационные eliminations — отдельная versioned Finance model, не raw dedup.

Join fact→account/product/legal entity/date/currency выполняется по surrogate version keys. Измерения выбираются по business effective time и принятой mapping version; нельзя присоединить нынешний тариф ко всей истории. Для поздно пришедшего измерения создаётся unknown surrogate со source key, затем управляемый reprocess; missing dimension не удаляет финансовый факт.

Клиентские связи M:N проходят bridge. Простое присоединение двух совместных владельцев удвоит сумму, поэтому финансовый итог считается **до** bridge либо после допустимого выбора/распределения роли. Customer 360 может показывать счёт каждому уполномоченному участнику, но такие представления не аддитивны между клиентами. Allocation weights не назначаются 50/50 по умолчанию.

## Закрытие и качество

Срез задаётся `report_release_id`, вектором source cutoffs, mapping version, FX version и code hash. Control tests проверяют unique facts, non-overlapping SCD2 intervals, orphan references, balanced transactions в принятом accounting scope, opening/movements/closing и totals по источнику/юрлицу/валюте. Exact decimal precision задаётся с учётом валют/инструментов; float/double для денег не используется.

Управленческая модель и регуляторная форма могут иметь разные определения и cutoffs. Форма строится из approved facts с отдельными business rules и sign-off; общий DWH не делает произвольный BI dashboard регуляторно корректным. Историческая поправка публикуется как новый release и при необходимости resubmission, сохраняя исходную версию.
