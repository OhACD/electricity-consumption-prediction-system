# Oslo Energy

An intentionally hands-on electricity data pipeline for AI research and learning. The project is built manually, from first principles, to make the data flow, persistence, and future machine-learning work easy to understand.

It currently collects monthly electricity consumption data for the NO1 electricity price area in Norway. The project is still under active development, and its architecture and scope will grow as new concepts are explored.

The project is named Oslo Energy because the original goal was to study electricity consumption around Oslo. The current SSB dataset is organized by electricity price area rather than municipality, so the implementation currently targets NO1, which covers south-eastern Norway.

## Quickstart

The easiest way to run Oslo Energy locally is to use Docker Compose for PostgreSQL and Python on the host machine.

Start PostgreSQL:

```bash
docker compose up -d
```

Create and activate a virtual environment, then install the project:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Apply the database migration:

```bash
docker compose exec -T postgres psql \
  -U oslo_energy \
  -d oslo_energy \
  < src/oslo_energy/database/migrations/001_create_electricity_observations.sql
```

Run the tests:

```bash
pytest
```

Run the ingestion pipeline:

```bash
python -m oslo_energy.pipeline.run_ingestion
```

The pipeline fetches the available monthly observations from SSB and stores them in PostgreSQL.

## Features

Oslo Energy currently provides:

1. An SSB PxWeb API client with timeout and HTTP error handling.
2. Ingestion of total electricity consumption for the NO1 price area.
3. Conversion of SSB JSON-stat2 responses into typed domain objects.
4. PostgreSQL persistence through a repository abstraction.
5. Idempotent writes protected by a database uniqueness constraint.
6. Transactional batch persistence with rollback on failure.
7. Unit and PostgreSQL integration tests for the core data flow.
8. A Docker Compose development database.

## How it works

The current data flow is:

```text
SSB PxWeb API
     |
     v
SSBClient
     |
     v
ElectricityIngestion
     |
     v
normalize()
     |
     v
ElectricityObservation
     |
     v
ElectricityRepository
     |
     v
PostgreSQL
```

The executable pipeline creates the SSB client, database connection, repository, and ingestion service. It then requests SSB table `14092`, normalizes the response, saves the observations, and closes the database connection.

The ingestion query selects:

- Consumer group: `0` (total)
- Price area: `NO1`
- Measure: `ForbrukTotal` (consumption)
- Time: all available months

The source currently provides monthly observations. A value such as `2026M08` is represented internally as `date(2026, 8, 1)`, using the first day of the month as the period convention.

## SSB Client

`SSBClient` owns communication with the Statistics Norway API. It handles HTTP requests, response decoding, timeouts, and HTTP failures. API failures are exposed as `SSBClientError` rather than leaking HTTP library details into the rest of the application.

The client does not decide which dataset or price area the application wants. Dataset selection belongs to the ingestion layer.

## Transformation

The normalization layer converts the external JSON-stat2 response into immutable `ElectricityObservation` values:

```python
ElectricityObservation(
    period=date(2026, 8, 1),
    price_area="NO1",
    consumer_group="0",
    consumption_mwh=1959910,
)
```

The source codes are preserved as identifiers. Human-readable labels can be added later through metadata or lookup tables.

## Database

PostgreSQL stores observations in the `electricity_observations` table:

| Column | Purpose |
| --- | --- |
| `id` | Internal identity key |
| `period` | First day of the observation month |
| `price_area_code` | SSB price-area code |
| `consumer_group_code` | SSB consumer-group code |
| `consumption_mwh` | Consumption in megawatt-hours |
| `ingested_at` | Time the record was persisted |

The table requires all observation fields, rejects negative consumption, and enforces uniqueness across:

```text
period + price_area_code + consumer_group_code
```

## Reliability Guarantees

## Idempotent ingestion

The repository uses `ON CONFLICT DO NOTHING` for the observation uniqueness key. Running the same ingestion twice does not create duplicate rows.

## Transactional persistence

Observations are saved as one batch. A successful batch is committed. If an insert fails, the repository rolls the transaction back so a partially written batch is not left in the database.

These guarantees are enforced at the persistence boundary and are not dependent only on application-level checks.

## Testing

The test suite is organized around architectural boundaries:

- Normalization tests use deterministic JSON-stat2 fixtures and require no network or database.
- Repository tests use PostgreSQL to verify persistence and idempotency.
- Rollback tests verify that a failed batch leaves no partial data behind.

The database tests expect the local PostgreSQL service to be running and the migration to have been applied.

## Database Inspection

Connect to the development database with:

```bash
docker compose exec postgres psql -U oslo_energy -d oslo_energy
```

Count stored observations:

```sql
SELECT COUNT(*)
FROM electricity_observations;
```

Inspect the monthly series:

```sql
SELECT
    period,
    price_area_code,
    consumer_group_code,
    consumption_mwh
FROM electricity_observations
ORDER BY period;
```

## Project Structure

```text
ml-prediction-pipeline/
|
+- src/oslo_energy/
|  +- ingestion/       SSB API communication
|  +- transformation/  JSON-stat2 normalization and domain model
|  +- database/        PostgreSQL connection, repository, and migration
|  +- pipeline/        Ingestion orchestration and executable entry point
|
+- tests/
|  +- database/        PostgreSQL repository and rollback tests
|
+- docker-compose.yml  Local PostgreSQL service
+- pyproject.toml      Python package and dependency configuration
```

## Current Limitations

1. The source data is monthly rather than hourly or daily.
2. Only the NO1 electricity price area is currently ingested.
3. Only the total consumer group and consumption measure are selected.
4. There is no forecasting model or prediction API yet.
5. There is no dashboard or automated cloud schedule yet.
6. Raw SSB responses are not archived.
7. There is no ingestion-run metadata or structured observability yet.
8. The normalizer supports the known application query shape rather than arbitrary JSON-stat2 datasets.
9. Database migrations are plain SQL files rather than a full migration framework.
10. Development credentials are local defaults and must not be used in production.

The current dataset is intentionally small. Its seasonal pattern makes it useful for proving the pipeline, but it also means future machine-learning work will need simple baselines and careful validation to avoid overfitting.

## Future Improvements

1. Add baseline forecasting models, including previous-month and seasonal-naive predictions.
2. Build feature extraction for lags, rolling statistics, and calendar seasonality.
3. Add forecast storage and model versioning.
4. Add ingestion-run tracking, structured logs, and freshness monitoring.
5. Schedule ingestion in a managed cloud environment.
6. Add an API or dashboard for observations and forecasts.
7. Expand the dataset and support additional price areas when needed.

## Engineering Decisions

- External systems are kept at the edges of the application.
- The SSB client knows how to communicate with SSB; ingestion knows what data to request.
- JSON-stat2 is converted at the normalization boundary so the rest of the application uses domain objects.
- SQL and transaction handling remain inside the repository.
- Database constraints provide a durable guarantee for idempotency and valid values.
- PostgreSQL is used instead of a data lake because the current dataset is small and benefits from relational constraints and simple local development.
- Additional infrastructure is deferred until the local ingestion pipeline is reliable.

## References

1. [Statistics Norway PxWeb API](https://data.ssb.no/api/pxwebapi/v2)
2. [SSB table 14092](https://www.ssb.no/en/statbank/table/14092)
3. [PostgreSQL documentation](https://www.postgresql.org/docs/)
4. [Docker Compose documentation](https://docs.docker.com/compose/)
