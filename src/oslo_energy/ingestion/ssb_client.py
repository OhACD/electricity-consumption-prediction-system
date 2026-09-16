"""
Main SSB client, responsible for interacting with the SSB API and fetching data.

Design:
- Communicate with the SSB PxWeb API and return SSB responses.

Owns:
- HTTP communication
- Base URL
- authentication if SSB ever requires it
- HTTP timeouts
- HTTP error handling
- API-specific request construction
- decoding JSON
- returning API responses
    
Note:
- The SSB API exposes separate endpoints for data and metadata.
"""

import json

import httpx

class SSBClientError(Exception):
    """Custom exception for SSBClient errors."""

class SSBClient:
    def __init__(self, 
                 base_url = "https://data.ssb.no/api/pxwebapi/v2",
                 timeout = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout


    # Fetch data from the SSB API
    # example usage:
    # client = SSBClient()
    # data = client.get_data("table_id")
    def get_data(self, table_id, query, output_format="json-stat2"):
        path = f"/tables/{table_id}/data"

        params = {
        "lang": "en",
        "outputFormat": output_format,
        }
        
        return self.request("POST", path, params=params, json=query)

    def get_metadata(self, table_id):
        path = f"/tables/{table_id}/metadata"

        params = {
            "lang": "en",
        }

        return self.request("GET", path, params=params)

    def request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"

        try:
            response = httpx.request(
                method,
                url,
                timeout=self.timeout,
                **kwargs,
            )

            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as exc:
            raise SSBClientError(
                f"SSB API request failed: {method} {url}"
            ) from exc

if __name__ == "__main__":
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
    metadata = client.get_metadata("14092")
    # data = client.get_data("14092", query)

    print(json.dumps(metadata, indent=2))
    # print(json.dumps(data, indent=2))