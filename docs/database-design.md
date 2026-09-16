# Database Design

## 1. Overview

The electricity consumption platform retrieves monthly electricity consumption data from Statistics Norway (SSB), transforms the source JSON-stat2 response into application-level observations, and persists those observations in PostgreSQL.

The database is responsible for:

* Persisting normalized electricity consumption observations.
* Enforcing data integrity constraints.
* Preventing duplicate observations.
* Supporting time-series queries by period and electricity price area.
* Recording when observations were ingested.

The initial database is intentionally small. Additional entities such as ingestion runs, source snapshots, and metadata reference tables can be introduced when the application requirements justify them.

---

## 2. Data Source

The initial data source is Statistics Norway (SSB) table `14092`.

The dataset provides:

* Electricity consumption.
* Consumer group.
* Electricity price area.
* Month.
* Measurement unit: MWh.

The initial application scope is:

* Consumer group: `0` — Total.
* Price area: `NO1` — South-eastern Norway.
* Metric: Consumption.
* Frequency: Monthly.

The SSB API represents months using values such as:

```text
2020M01
2020M02
2026M08
```

The application domain represents these periods as the first day of the corresponding month when persisted in PostgreSQL:

```text
2020-01-01
2020-02-01
2026-08-01
```

This allows PostgreSQL to treat the observation period as a temporal value rather than an arbitrary string.

---

# 3. Database Responsibilities

The database should enforce invariants that must remain true regardless of which application component writes the data.

The database must guarantee that:

1. Every observation has a period.
2. Every observation has a price area.
3. Every observation has a consumer group.
4. Every observation has a consumption value.
5. Consumption cannot be negative.
6. A single period/price-area/consumer-group combination can occur only once.

Application code is responsible for:

* Retrieving data from SSB.
* Interpreting the SSB response.
* Transforming source representations into domain objects.
* Handling API errors.
* Coordinating ingestion.

The database should not be responsible for interpreting SSB's JSON-stat2 format.

---

# 4. Entity Model

The initial database contains one primary domain entity:

```text
ElectricityObservation
```

An electricity observation represents the measured electricity consumption for:

```text
period
+
price area
+
consumer group
```

For example:

```text
Period:          2026-08-01
Price area:      NO1
Consumer group:  0
Consumption:     1,959,910 MWh
```

This represents one unique observation.

---

# 5. Entity Relationship

The initial schema contains a single core table:

```text
┌──────────────────────────────────────────────┐
│           electricity_observations           │
├──────────────────────────────────────────────┤
│ id                                           │
│ period                                       │
│ price_area_code                              │
│ consumer_group_code                          │
│ consumption_mwh                              │
│ ingested_at                                  │
└──────────────────────────────────────────────┘
```

There are currently no foreign-key relationships because price areas and consumer groups are stored using their SSB source codes.

Reference tables may be introduced later if the application begins supporting multiple datasets, dynamic metadata, or user-facing metadata management.

---

# 6. Table: electricity_observations

## Purpose

Stores normalized electricity consumption observations retrieved from SSB.

## Columns

| Column                | PostgreSQL Type   | Nullable | Description                                                  |
| --------------------- | ----------------- | -------: | ------------------------------------------------------------ |
| `id`                  | `BIGINT` identity |       No | Internal primary key                                         |
| `period`              | `DATE`            |       No | First day of the month represented by the observation        |
| `price_area_code`     | `VARCHAR(10)`     |       No | SSB electricity price-area code, e.g. `NO1`                  |
| `consumer_group_code` | `VARCHAR(10)`     |       No | SSB consumer-group code, e.g. `0`                            |
| `consumption_mwh`     | `BIGINT`          |       No | Electricity consumption measured in MWh                      |
| `ingested_at`         | `TIMESTAMPTZ`     |       No | Timestamp at which the application persisted the observation |

---

# 7. Primary Key

The table uses an internal surrogate primary key:

```text
id
```

The primary key exists to provide a stable database identifier for a row.

It is not the domain identity of an electricity observation.

The domain identity is represented by:

```text
(period, price_area_code, consumer_group_code)
```

---

# 8. Observation Uniqueness

The following combination must be unique:

```text
period
price_area_code
consumer_group_code
```

This is enforced using a database-level unique constraint.

Conceptually:

```sql
UNIQUE (
    period,
    price_area_code,
    consumer_group_code
)
```

This means the database cannot contain two observations such as:

```text
2026-08-01 | NO1 | 0
2026-08-01 | NO1 | 0
```

This constraint is important for idempotent ingestion.

If the same SSB data is retrieved more than once, the database should not create duplicate observations.

---

# 9. Data Integrity Constraints

## 9.1 Required fields

All observation fields are required.

The following columns are `NOT NULL`:

```text
period
price_area_code
consumer_group_code
consumption_mwh
ingested_at
```

## 9.2 Non-negative consumption

Electricity consumption cannot be negative in this dataset.

The database should enforce:

```sql
CHECK (consumption_mwh >= 0)
```

This prevents invalid values from entering the database even if an application-level validation is accidentally bypassed.

## 9.3 Non-empty codes

Price-area and consumer-group codes should not be empty strings.

Application validation should normally prevent this, while the database can additionally enforce the invariant if required.

---

# 10. Period Representation

SSB represents monthly periods using the format:

```text
YYYYMmm
```

Examples:

```text
2020M01
2024M12
2026M08
```

The database does not store this representation directly.

Instead:

```text
2020M01 → 2020-01-01
2024M12 → 2024-12-01
2026M08 → 2026-08-01
```

The date represents the month containing the observation.

The application should treat the value as a monthly period rather than as an arbitrary calendar day.

This representation provides natural chronological ordering and simplifies time-range queries.

---

# 11. Source Codes

The database stores the SSB source codes rather than duplicating their human-readable labels.

Examples:

```text
price_area_code = NO1
consumer_group_code = 0
```

The codes provide stable identifiers originating from the source dataset.

Human-readable labels such as:

```text
NO1 → South-eastern Norway
0   → Total
```

are metadata and should not be duplicated into every observation row unless future requirements justify doing so.

This avoids storing repeated descriptive data and preserves the source identifiers used by the API.

---

# 12. Units

The initial application is specifically designed around electricity consumption measured in MWh.

Therefore the observation stores:

```text
consumption_mwh
```

rather than using a generic:

```text
value
unit
```

model.

This makes the database schema explicit about the meaning of the stored value.

If the application later expands to support multiple measurements or datasets with different units, the schema can be reconsidered at that point.

---

# 13. Ingestion Timestamp

`ingested_at` records when the application persisted the observation.

It does not represent when the electricity was consumed.

These concepts are intentionally separate:

```text
period
    ↓
When the measurement applies to

ingested_at
    ↓
When our system stored the measurement
```

For example:

```text
period       = 2026-08-01
ingested_at  = 2026-09-17 01:45:23+03
```

This distinction becomes important when ingestion is automated.

---

# 14. Indexing

The unique constraint on:

```text
(period, price_area_code, consumer_group_code)
```

provides an index suitable for enforcing uniqueness.

The primary expected access pattern is retrieving observations for a price area ordered chronologically:

```sql
SELECT *
FROM electricity_observations
WHERE price_area_code = 'NO1'
ORDER BY period;
```

Additional indexes should be introduced based on observed query patterns rather than added speculatively.

The initial dataset is small enough that excessive indexing would provide little benefit while increasing write complexity.

---

# 15. Idempotent Ingestion

The ingestion pipeline is expected to be safely repeatable.

For example, running the ingestion process twice against the same SSB dataset should not create duplicate rows.

The database contributes to this property through:

```text
UNIQUE(
    period,
    price_area_code,
    consumer_group_code
)
```

The repository layer will eventually use this constraint when implementing an insert/upsert strategy.

The desired behavior is:

```text
First ingestion
    ↓
observation does not exist
    ↓
INSERT


Repeated ingestion
    ↓
observation already exists
    ↓
do not create duplicate
```

The exact behavior for changed historical values will be defined separately when update semantics are implemented.

---

# 16. Transaction Boundary

Database writes should be performed within a transaction.

An ingestion operation should avoid leaving the database in an unintentionally partial state.

For example, if an ingestion contains 80 observations:

```text
BEGIN
    insert observations
COMMIT
```

If an unrecoverable error occurs:

```text
BEGIN
    insert observations
    error
ROLLBACK
```

The repository layer should own transaction handling rather than the normalization layer.

---

# 17. What Is Deliberately Not in the Initial Schema

The following are intentionally excluded from the first database version:

### Ingestion runs

A future table may record:

```text
ingestion_runs
```

containing:

* start time
* completion time
* status
* records fetched
* records inserted
* error information

This becomes more valuable when scheduled Lambda ingestion is introduced.

### Raw SSB responses

Raw JSON-stat2 responses may eventually be archived for reproducibility and debugging, potentially in object storage such as S3.

They do not belong in the normalized observation table.

### Metadata tables

Dedicated tables for:

```text
price_areas
consumer_groups
```

may be introduced if the application begins supporting multiple areas/groups dynamically.

### Forecast results

Machine-learning predictions should not be stored in the observation table.

Forecasts represent model output rather than source observations and should eventually have their own domain model.

---

# 18. Future Architecture

The initial database is designed to evolve toward:

```text
                         SSB
                          │
                          ▼
                    SSBClient
                          │
                          ▼
                       fetch
                          │
                          ▼
                     normalize
                          │
                          ▼
              ElectricityObservation
                          │
                          ▼
                     Repository
                          │
                          ▼
                    PostgreSQL
                    ┌─────┴─────┐
                    │           │
                    ▼           ▼
               Dashboard    Forecasting
```

As the system matures, ingestion metadata can be introduced:

```text
                    PostgreSQL
                    ┌─────┴──────────┐
                    │                │
                    ▼                ▼
             ingestion_runs    observations
```

This keeps operational metadata separate from domain measurements.

---

# 19. Design Principles

The database design follows these principles:

### Keep the domain model explicit

Column names should communicate what the data represents.

### Preserve source identity

SSB codes are retained rather than replacing them with presentation labels.

### Enforce invariants at the database boundary

Important correctness rules should not exist only in Python.

### Prefer idempotent operations

Repeated ingestion should not create duplicate observations.

### Avoid premature normalization
