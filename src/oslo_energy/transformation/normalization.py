"""
Normalization functions for Oslo Energy data.

These functions are responsible for transforming raw data into a standardized format suitable for further analysis and processing.

Design:
- Prefer typed python for future maintainability and clarity
"""

from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class ElectricityObservation:
    period: date
    price_area: str
    consumer_group: str
    consumption_mwh: int

# Helper function to parse date strings in the format "YYYYMM" into datetime.date objects.
def _parse_date(value: str) -> date:
    year, month = value.split("M")
    return date(
        year=int(year),
        month=int(month),
        day=1
    )

def normalize(data: dict) -> list[ElectricityObservation]:
    dimensions = data["dimension"]

    consumer_group = _get_single_category(
        dimensions["Forbrukargruppe"]
    )

    price_area = _get_single_category(
        dimensions["Prisomraade"]
    )

    periods = _get_categories(
        dimensions["Tid"]
    )

    values = data["value"]

    if len(periods) != len(values):
        raise ValueError(
            "Number of periods does not match number of values"
        )

    return [
        ElectricityObservation(
            period=_parse_date(period),
            price_area=price_area,
            consumer_group=consumer_group,
            consumption_mwh=value,
        )
        for period, value in zip(periods, values)
    ]


def _get_categories(dimension: dict) -> list[str]:
    return list(
        dimension["category"]["index"].keys()
    )


def _get_single_category(dimension: dict) -> str:
    categories = _get_categories(dimension)

    if len(categories) != 1:
        raise ValueError(
            "Expected exactly one category"
        )

    return categories[0]

if __name__ == "__main__":
    from oslo_energy.ingestion.ssb_client import SSBClient

    query = {
        "selection": [
            {
                "variableCode": "Forbrukargruppe",
                "valueCodes": ["0"],
            },
            {
                "variableCode": "Prisomraade",
                "valueCodes": ["NO1"],
            },
            {
                "variableCode": "ContentsCode",
                "valueCodes": ["ForbrukTotal"],
            },
            {
                "variableCode": "Tid",
                "valueCodes": ["*"],
            },
        ]
    }
    client = SSBClient()
    raw_data = client.get_data("14092", query)
    normalized_data = normalize(raw_data)
    for observation in normalized_data:
        print(observation)