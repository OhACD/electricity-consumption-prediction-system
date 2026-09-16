from datetime import date

from oslo_energy.database.repository import ElectricityRepository
from oslo_energy.transformation.normalization import ElectricityObservation


def test_save_observation(connection):
    repository = ElectricityRepository(connection)

    observation = ElectricityObservation(
        period=date(2030, 1, 1),
        price_area="NO1",
        consumer_group="0",
        consumption_mwh=100000,
    )

    repository.save_observations([observation])

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT period, price_area_code, consumer_group_code, consumption_mwh
            FROM electricity_observations
            WHERE period = %s
            """,
            (observation.period,),
        )

        row = cursor.fetchone()

    assert row == (
        date(2030, 1, 1),
        "NO1",
        "0",
        100000,
    )


def test_save_observation_is_idempotent(connection):
    repository = ElectricityRepository(connection)

    observation = ElectricityObservation(
        period=date(2030, 2, 1),
        price_area="NO1",
        consumer_group="0",
        consumption_mwh=200000,
    )

    repository.save_observations([observation])
    repository.save_observations([observation])

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM electricity_observations
            WHERE period = %s
              AND price_area_code = %s
              AND consumer_group_code = %s
            """,
            (
                observation.period,
                observation.price_area,
                observation.consumer_group,
            ),
        )

        count = cursor.fetchone()[0]

    assert count == 1