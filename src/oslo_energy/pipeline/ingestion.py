from oslo_energy.transformation.normalization import normalize


class ElectricityIngestion:
    def __init__(self, client, repository):
        self.client = client
        self.repository = repository

    def run(self) -> int:
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

        raw_data = self.client.get_data("14092", query)
        observations = normalize(raw_data)

        self.repository.save_observations(observations)

        return len(observations)