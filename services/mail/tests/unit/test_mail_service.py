from unittest.mock import AsyncMock, patch

from src.kafka.consumer import handle_event
from src.services.mail import MailService


class TestHandleEvent:
    async def test_user_registered_calls_send_welcome(self):
        mail_service = AsyncMock(spec=MailService)
        event = {
            'event_type': 'user_registered',
            'payload': {'email': 'alice@example.com', 'username': 'alice'},
        }
        await handle_event(event, mail_service)
        mail_service.send_welcome_email.assert_awaited_once_with(
            to='alice@example.com', username='alice'
        )

    async def test_unknown_event_type_does_not_raise(self):
        mail_service = AsyncMock(spec=MailService)
        event = {'event_type': 'unknown_event', 'payload': {}}
        await handle_event(event, mail_service)
        mail_service.send_welcome_email.assert_not_awaited()

    async def test_missing_event_type_does_not_raise(self):
        mail_service = AsyncMock(spec=MailService)
        await handle_event({}, mail_service)
        mail_service.send_welcome_email.assert_not_awaited()


class TestMailService:
    async def test_send_welcome_email(self):
        with patch('src.services.mail.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
            service = MailService()
            await service.send_welcome_email(to='alice@example.com', username='alice')
            mock_send.assert_awaited_once()
            call_kwargs = mock_send.call_args
            msg = call_kwargs.args[0]
            assert msg['To'] == 'alice@example.com'
            assert 'alice' in msg.get_payload(decode=True).decode()
