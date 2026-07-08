import logging
from email.mime.text import MIMEText

import aiosmtplib

from src.core.config import settings

logger = logging.getLogger(__name__)


class MailService:
    async def send_welcome_email(self, to: str, username: str) -> None:
        body = f'Привет, {username}!\n\nДобро пожаловать в Gallery.'
        message = MIMEText(body, 'plain', 'utf-8')
        message['From'] = settings.smtp.from_email
        message['To'] = to
        message['Subject'] = 'Добро пожаловать в Gallery!'
        await aiosmtplib.send(
            message,
            hostname=settings.smtp.host,
            port=settings.smtp.port,
        )
        logger.info('Welcome email sent to %s', to)
