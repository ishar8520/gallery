import logging
from email.mime.text import MIMEText

import aiosmtplib
import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class MailService:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self.http_client = http_client

    async def _get_short_url(self, url: str, ttl: int) -> str:
        resp = await self.http_client.post(
            f'{settings.link_service.url}/link/api/v1/links',
            json={'url': url, 'ttl': ttl},
            timeout=5.0,
        )
        resp.raise_for_status()
        return resp.json()['short_url']

    async def send_confirmation_email(self, to: str, username: str, token: str) -> None:
        confirm_url = f'{settings.auth.public_url}/confirm?token={token}'
        try:
            short_url = await self._get_short_url(confirm_url, ttl=86400)
        except Exception:
            logger.exception('Failed to get short URL, falling back to full URL')
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

    async def send_reset_password_email(self, to: str, username: str, token: str) -> None:
        reset_url = f'{settings.auth.public_url}/reset-password?token={token}'
        try:
            short_url = await self._get_short_url(reset_url, ttl=3600)
        except Exception:
            logger.exception('Failed to get short URL, falling back to full URL')
            short_url = reset_url

        body = (
            f'Привет, {username}!\n\n'
            f'Для сброса пароля перейдите по ссылке:\n{short_url}\n\n'
            f'Ссылка действительна 1 час. Если вы не запрашивали сброс пароля — просто '
            f'проигнорируйте это письмо.'
        )
        message = MIMEText(body, 'plain', 'utf-8')
        message['From'] = settings.smtp.from_email
        message['To'] = to
        message['Subject'] = 'Сброс пароля в Gallery'
        await aiosmtplib.send(
            message,
            hostname=settings.smtp.host,
            port=settings.smtp.port,
        )
        logger.info('Password reset email sent to %s', to)
