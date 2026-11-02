# Task3 — целевая платформа данных

Выбран гибрид: PostgreSQL DWH для контролируемой отчётности, Iceberg Lakehouse для больших исторических/событийных данных и общая платформа управления. Элементы Data Mesh вводятся через владельцев и контракты пяти data-продуктов, без полной децентрализации инфраструктуры.

| Документ | Назначение |
|---|---|
| [target-data-architecture.md](target-data-architecture.md) | Границы систем и управление целевой платформой |
| [architecture-options.md](architecture-options.md) | DWH/PostgreSQL, Lakehouse и Data Mesh: сравнение и решение |
| [dwh-lakehouse.md](dwh-lakehouse.md) | Распределение данных, Iceberg/Trino и ограничения |
| [data-pipelines.md](data-pipelines.md) | Шесть пайплайнов, простой MVP ELT и два сценария больших данных |
| [analytical-model.md](analytical-model.md) | Звезда финансовых движений, grain и защита от двойного счёта |
| [data-products.md](data-products.md) | Контракты, owners и потребители пяти продуктов |

Диаграммы: [целевая платформа PNG](diagrams/target-12m.png) ([PlantUML](diagrams/target-12m.puml)), [аналитическая модель PNG](diagrams/analytical-star.png) ([PlantUML](diagrams/analytical-star.puml)).
