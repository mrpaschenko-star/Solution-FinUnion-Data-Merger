# Владение и изменение данных

Роли предлагаются для назначения. **Data Owner** отвечает за смысл/допуск использования, **Data Steward** — за правила и разбор качества; технический Producer обеспечивает контракт. Data Office координирует, но не заменяет финансового или продуктового владельца.

| Сущности | Data Owner | Data Steward | Producer | Consumer | Правила изменения | Обязательное качество |
|---|---|---|---|---|---|---|
| E01 Клиент | Руководитель клиентского/KYC домена с ответственностью обеих организаций | KYC/CRM stewards FU/RB | Onboarding/CRM/Core → Hub | CRM, Core, риск, разрешённый BI | Golden поля через утверждённый workflow; conflicts вручную | Тип лица, обязательные по сценарию идентификаторы, verification, duplicate/conflict review |
| E02 Crosswalk | Party owner / Data Office governance | MDM steward | Hub matching | Все consumers enterprise ID | Версионированный merge/unmerge, dual review спорных случаев | Один active mapping source key, отсутствие циклических aliases, lineage evidence |
| E03 Счёт | Операционный счётный бизнес | Core data steward + Finance control | FU/RB Core | Cards/Loans, DWH, профиль клиента | Только активный owner, договорное право, maker-checker для критичных corrections | Ключ, валюта, legal entity, status lifecycle, договорная роль |
| E04 Карта | Карточный бизнес | Processing steward | FU/RB Cards | Core, CRM, fraud, DWH | Выпуск/статусы через процессинг, перевыпуск как связанный lifecycle | Token, linkage to account, chronology, status mapping |
| E05 Кредит | Кредитный бизнес | Loans steward + риск/Finance | FU/RB Loans | Core, риск, DWH | Версия условий/графика по кредитному процессу | Principal/interest/fees раздельно, due-date и ledger reconciliation |
| E06/E14 Договор и стороны | Владелец соответствующего продукта + Legal | Договорный steward | Core/Loans/onboarding | CRM, DWH, audit | Подписанный evidence, тип/срок полномочий; не менять через merge | Product version, legal entity, роли/даты, документ и отсутствие конфликтов |
| E07/E08 Учёт | Финансовый департамент | Accounting/control steward | Core/approved subledger | DWH, Finance, регуляторный процесс | Posted facts корректируются отдельными записями | Debit/credit, completeness, opening + movements = closing, source totals |
| E09 Платёж | Платёжный бизнес | Payment operations steward | Core/payment execution | Учёт, каналы, DWH | Только active executor; неизвестный исход сверяется | Business idempotency, amount/currency, state transitions и correlation |
| E10 Продукт | Product management по линии бизнеса | Product/catalog steward | Продуктовые команды → directory | CRM/Core/Cards/Loans, BI | Утверждение версии/срока, отдельно execution rules | Непересекающиеся effective intervals, cross-bank equivalence, tariff history |
| E11 Обращение | Контактный центр | CRM/case steward | FU/RB CRM/каналы | Менеджеры, service BI | Workflow owner; перевод active case с полной историей | Customer link, status timestamps, duplicate detection, sensitive text handling |
| E12 Справочник | Отдельный owner каждого dictionary | Reference steward | Owner → Hub/MDM | Все системы/витрины | Maker-checker, effective dates, deprecate вместо удаления used code | Code uniqueness, mapping coverage, referential checks |
| E13 Согласие | Владелец процесса обработки + Legal/ИБ | Privacy steward | Канал/consent register | CRM, маркетинг, Hub, аналитика | Purpose/legal basis, отзыв/evidence; merge не расширяет разрешения | Validity, revocation propagation, запрещённое использование блокируется |
| E15 Курс | Treasury + Finance | Treasury reference steward | Утверждённый provider/feed | DWH, accounting consumers | Approved rate type/date/source; correction новой версией | Decimal precision, currencies, as-of/quote direction, missing-day handling |

## Контракты и исключения

Каждый data-продукт/поток регистрирует schema version, owner/steward, allowed purposes, quality rules, freshness target, retention, lineage и incident route. Schema changes проходят совместимость с consumers; изменение бизнес-смысла требует новой contract version, а не только nullable-колонки.

Hard financial/identity failures останавливают публикацию затронутого scope и попадают в quarantine; soft enrichment gaps могут публиковаться с quality flag, если утверждено потребителем. Нельзя молча исключить проблемные проводки и объявить отчёт полным. Исправление выполняется в master либо контролируемой mapping version; правка DWH «до сходящихся сумм» запрещена.

Для выдачи отчётной версии нужны maker/checker от Finance, подтверждение технической полноты от platform owner и допуск ИБ для нового scope. DataHub отражает решения и состояние, но не заменяет runtime enforcement в источниках, брокере, SQL engines и BI.
