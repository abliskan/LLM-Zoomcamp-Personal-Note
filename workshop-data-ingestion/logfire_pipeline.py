import argparse
import os
from datetime import UTC, datetime, timedelta

import dlt
import requests
from dotenv import load_dotenv


QUERY = 'SELECT * FROM records'


@dlt.resource(name='spans', write_disposition='replace')
def logfire_spans(read_token: str, region: str, days: int):
    """Fetch Logfire records as nested JSON so dlt can normalize the payload."""
    min_timestamp = datetime.now(UTC) - timedelta(days=days)
    response = requests.post(
        f'https://logfire-{region}.pydantic.dev/v2/query',
        headers={
            'Authorization': f'Bearer {read_token}',
            'Accept': 'application/json',
        },
        json={
            'sql': QUERY,
            'min_timestamp': min_timestamp.isoformat(),
            'limit': 10_000,
        },
        timeout=60,
    )
    response.raise_for_status()
    yield from response.json()['data']


def main():
    parser = argparse.ArgumentParser(
        description='Load Logfire traces into a local DuckDB database.'
    )
    parser.add_argument('--days', type=int, default=30)
    args = parser.parse_args()

    load_dotenv()
    read_token = os.environ.get('LOGFIRE_READ_TOKEN')
    if not read_token:
        raise RuntimeError('Set LOGFIRE_READ_TOKEN in .env before loading traces.')

    region = os.environ.get('LOGFIRE_REGION', 'us').lower()
    if region not in {'us', 'eu'}:
        raise ValueError('LOGFIRE_REGION must be either "us" or "eu".')

    pipeline = dlt.pipeline(
        pipeline_name='logfire_pipeline',
        destination='duckdb',
        dataset_name='agent_traces',
    )
    load_info = pipeline.run(logfire_spans(read_token, region, args.days))
    print(load_info)


if __name__ == '__main__':
    main()