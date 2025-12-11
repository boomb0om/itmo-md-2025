# dbt

Lightweight dbt layer that models data from the raw warehouse schema.

## Structure
```
dbt/
├── models/          # staging, intermediate, and marts models
├── seeds/           # reference CSVs for small lookup tables
├── snapshots/       # slowly changing dimension snapshots
├── macros/          # shared transformations and helpers
└── tests/           # schema + data tests
```

## Workflow
- Sources point to the `raw_*` tables populated by Airflow.
- Staging models clean and type-cast Mongo payloads.
- Marts join staged price and news data for downstream analytics.
- Run locally with `dbt build --profiles-dir .` once a profile is configured.

