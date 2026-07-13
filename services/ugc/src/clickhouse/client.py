import clickhouse_connect

from src.core.config import settings

_client = None


def get_client() -> clickhouse_connect.driver.Client:
    return _client


async def init_clickhouse() -> None:
    global _client
    _client = clickhouse_connect.get_client(
        host=settings.clickhouse.host,
        port=settings.clickhouse.port,
        username=settings.clickhouse.user,
        password=settings.clickhouse.password,
    )

    _client.command(f'CREATE DATABASE IF NOT EXISTS {settings.clickhouse.database}')

    _client.command(f"""
        CREATE TABLE IF NOT EXISTS {settings.clickhouse.database}.photo_events (
            event_type LowCardinality(String),
            user_id    String,
            photo_id   String,
            title      String,
            timestamp  DateTime64(3, 'UTC')
        ) ENGINE = MergeTree()
        ORDER BY (timestamp, user_id)
    """)

    _client.command(f"""
        CREATE TABLE IF NOT EXISTS {settings.clickhouse.database}.auth_events (
            user_id   String,
            provider  LowCardinality(String),
            timestamp DateTime64(3, 'UTC')
        ) ENGINE = MergeTree()
        ORDER BY (timestamp, user_id)
    """)

    _client.command(f"""
        CREATE TABLE IF NOT EXISTS {settings.clickhouse.database}.click_events (
            user_id   String,
            page      String,
            element   String,
            timestamp DateTime64(3, 'UTC')
        ) ENGINE = MergeTree()
        ORDER BY (timestamp, user_id)
    """)
