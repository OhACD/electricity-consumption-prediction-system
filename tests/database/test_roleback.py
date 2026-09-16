from datetime import date

import pytest

from oslo_energy.database.repository import ElectricityRepository
from oslo_energy.transformation.normalization import ElectricityObservation


def test_save_observations_rolls_back_on_failure(connection):
    repository = ElectricityRepository(connection)

    observations = [
        ElectricityObservation(
            period=date(2030, 3, 1),
            price_area="NO1",
            consumer_group="0",
            consumption_mwh=100000,
        ),
        ElectricityObservation(
            period=date(2030, 4, 1),
            price_area="NO1",
            consumer_group="0",
            consumption_mwh=-500,
        ),
    ]

    with pytest.raises(Exception):
        repository.save_observations(observations)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM electricity_observations
            WHERE period IN ('2030-03-01', '2030-04-01')
            """
        )

        count = cursor.fetchone()[0]

    assert count == 0