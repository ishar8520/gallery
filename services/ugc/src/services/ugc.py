import logging
from datetime import datetime, timezone

import clickhouse_connect

from src.clickhouse.client import get_client
from src.core.config import settings

logger = logging.getLogger(__name__)

DB = settings.clickhouse.database


class UGCService:
    def __init__(self) -> None:
        self.client: clickhouse_connect.driver.Client = get_client()

    # ── Writers ───────────────────────────────────────────────────────────────

    def record_photo_event(
        self, event_type: str, user_id: str, photo_id: str, title: str, timestamp: str
    ) -> None:
        ts = _parse_ts(timestamp)
        self.client.insert(
            f'{DB}.photo_events',
            [[event_type, user_id, photo_id, title, ts]],
            column_names=['event_type', 'user_id', 'photo_id', 'title', 'timestamp'],
        )

    def record_auth_event(self, user_id: str, provider: str, timestamp: str) -> None:
        ts = _parse_ts(timestamp)
        self.client.insert(
            f'{DB}.auth_events',
            [[user_id, provider, ts]],
            column_names=['user_id', 'provider', 'timestamp'],
        )

    def record_click_event(self, user_id: str, page: str, element: str) -> None:
        ts = datetime.now(timezone.utc)
        self.client.insert(
            f'{DB}.click_events',
            [[user_id, page, element, ts]],
            column_names=['user_id', 'page', 'element', 'timestamp'],
        )

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_photo_stats(self) -> dict:
        rows = self.client.query(f"""
            SELECT
                event_type,
                toDate(timestamp) AS day,
                count() AS cnt
            FROM {DB}.photo_events
            GROUP BY event_type, day
            ORDER BY day DESC
            LIMIT 90
        """).result_rows
        return {
            'by_day': [
                {'event_type': r[0], 'day': str(r[1]), 'count': r[2]} for r in rows
            ],
            'total_uploaded': self._scalar(
                f"SELECT count() FROM {DB}.photo_events WHERE event_type = 'photo_uploaded'"
            ),
            'total_deleted': self._scalar(
                f"SELECT count() FROM {DB}.photo_events WHERE event_type = 'photo_deleted'"
            ),
        }

    def get_auth_stats(self) -> dict:
        rows = self.client.query(f"""
            SELECT
                provider,
                toDate(timestamp) AS day,
                count() AS cnt
            FROM {DB}.auth_events
            GROUP BY provider, day
            ORDER BY day DESC
            LIMIT 90
        """).result_rows
        by_provider = self.client.query(f"""
            SELECT provider, count() AS cnt
            FROM {DB}.auth_events
            GROUP BY provider
            ORDER BY cnt DESC
        """).result_rows
        return {
            'by_day': [
                {'provider': r[0], 'day': str(r[1]), 'count': r[2]} for r in rows
            ],
            'by_provider': [{'provider': r[0], 'count': r[1]} for r in by_provider],
            'total': self._scalar(f'SELECT count() FROM {DB}.auth_events'),
        }

    def get_click_stats(self) -> dict:
        top_pages = self.client.query(f"""
            SELECT page, count() AS cnt
            FROM {DB}.click_events
            GROUP BY page
            ORDER BY cnt DESC
            LIMIT 20
        """).result_rows
        top_elements = self.client.query(f"""
            SELECT element, count() AS cnt
            FROM {DB}.click_events
            GROUP BY element
            ORDER BY cnt DESC
            LIMIT 20
        """).result_rows
        return {
            'top_pages': [{'page': r[0], 'count': r[1]} for r in top_pages],
            'top_elements': [{'element': r[0], 'count': r[1]} for r in top_elements],
            'total': self._scalar(f'SELECT count() FROM {DB}.click_events'),
        }

    def _scalar(self, query: str) -> int:
        result = self.client.query(query).result_rows
        return result[0][0] if result else 0


def _parse_ts(timestamp: str) -> datetime:
    try:
        return datetime.fromisoformat(timestamp)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def get_ugc_service() -> UGCService:
    return UGCService()
