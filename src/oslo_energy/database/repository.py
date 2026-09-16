from collections.abc import Iterable

from oslo_energy.transformation.normalization import ElectricityObservation


class ElectricityRepository:
    def __init__(self, connection):
        self.connection = connection

    def save_observations(
    self,
    observations: Iterable[ElectricityObservation],
    ) -> None:
        query = """
            INSERT INTO electricity_observations (
                period,
                price_area_code,
                consumer_group_code,
                consumption_mwh
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (
                period,
                price_area_code,
                consumer_group_code
            )
            DO NOTHING
        """

        try:
            with self.connection.cursor() as cursor:
                for observation in observations:
                    cursor.execute(
                        query,
                        (
                            observation.period,
                            observation.price_area,
                            observation.consumer_group,
                            observation.consumption_mwh,
                        ),
                    )

            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

if __name__ == "__main__":
    from datetime import date

    from oslo_energy.database.connection import (
        create_connection,
        load_config,
    )

    observation = ElectricityObservation(
        period=date(2026, 8, 1),
        price_area="NO1",
        consumer_group="0",
        consumption_mwh=1959910,
    )

    connection = create_connection(load_config())

    repository = ElectricityRepository(connection)

    repository.save_observations([observation])

    connection.close()

    print("Observation saved.")