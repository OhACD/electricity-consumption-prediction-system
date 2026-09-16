from oslo_energy.database.connection import (
    create_connection,
    load_config,
)
from oslo_energy.database.repository import ElectricityRepository
from oslo_energy.ingestion.ssb_client import SSBClient
from oslo_energy.pipeline.ingestion import ElectricityIngestion


def main():
    client = SSBClient()

    connection = create_connection(load_config())

    try:
        repository = ElectricityRepository(connection)

        ingestion = ElectricityIngestion(
            client=client,
            repository=repository,
        )

        count = ingestion.run()

        print(f"Processed {count} observations")
    finally:
        connection.close()


if __name__ == "__main__":
    main()