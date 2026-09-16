import pytest

from oslo_energy.database.connection import create_connection, load_config


@pytest.fixture
def connection():
    connection = create_connection(load_config())

    yield connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM electricity_observations
            WHERE period >= '2030-01-01'
              AND period < '2031-01-01'
            """
        )

    connection.commit()
    connection.close()