import logging
from email.mime.text import MIMEText

import aiosmtplib
import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class MailService:
    async def _get_short_url(self, url: str, ttl: int) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f'{settings.link_service.url}/link/api/v1/links',
                json={'url': url, 'ttl': ttl},
                timeout=5.0,
            )
            resp.raise_for_status()
            return resp.json()['short_url']

    async def send_confirmation_email(self, to: str, username: str, token: str) -> None:
        confirm_url = f'{settings.auth.public_url}/auth/api/v1/confirm?token={token}'
        try:
            short_url = await self._get_short_url(confirm_url, ttl=86400)
        except Exception:
            logger.exception('Failed to shorten URL, using full URL')
            short_url = confirm_url

        body = (
            f'Привет, {username}!\n\n'
            f'Для подтверждения регистрации перейдите по ссылке:\n{short_url}\n\n'
            f'Ссылка действительна 24 часа.'
        )
        message = MIMEText(body, 'plain', 'utf-8')
        message['From'] = settings.smtp.from_email
        message['To'] = to
        message['Subject'] = 'Подтверждение регистрации в Gallery'
        await aiosmtplib.send(
            message,
            hostname=settings.smtp.host,
            port=settings.smtp.port,
        )
        logger.info('Confirmation email sent to %s', to)
