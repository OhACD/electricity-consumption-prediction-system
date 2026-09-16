"""
Establishes a connection to the Oslo Energy PostgreSQL database.
"""

from dataclasses import dataclass
import os

import psycopg

@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str

def load_config() -> DatabaseConfig:
    return DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        name=os.getenv("POSTGRES_DB", "oslo_energy"),
        user=os.getenv("POSTGRES_USER", "oslo_energy"),
        password=os.getenv("POSTGRES_PASSWORD", "oslo_energy_dev")
    )

def create_connection(config: DatabaseConfig):
    return psycopg.connect(
        host=config.host,
        port=config.port,
        dbname=config.name,
        user=config.user,
        password=config.password
    )

if __name__ == "__main__":
    config = load_config()

    with create_connection(config) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), version()")
            print(cursor.fetchone())
