from unittest.mock import AsyncMock, patch

import httpx

from src.kafka.consumer import handle_event
from src.services.mail import MailService


def make_service(mock_client=None):
    client = mock_client or AsyncMock(spec=httpx.AsyncClient)
    return MailService(http_client=client)


class TestHandleEvent:
    async def test_confirmation_requested_calls_send_confirmation(self):
        mail_service = AsyncMock(spec=MailService)
        event = {
            'event_type': 'email_confirmation_requested',
            'payload': {
                'email': 'alice@example.com',
                'username': 'alice',
                'token': 'test-token-123',
            },
        }
        await handle_event(event, mail_service)
        mail_service.send_confirmation_email.assert_awaited_once_with(
            to='alice@example.com',
            username='alice',
            token='test-token-123',
        )

    async def test_unknown_event_type_does_not_raise(self):
        mail_service = AsyncMock(spec=MailService)
        event = {'event_type': 'unknown_event', 'payload': {}}
        await handle_event(event, mail_service)
        mail_service.send_confirmation_email.assert_not_awaited()

    async def test_missing_event_type_does_not_raise(self):
        mail_service = AsyncMock(spec=MailService)
        await handle_event({}, mail_service)
        mail_service.send_confirmation_email.assert_not_awaited()


class TestMailService:
    async def test_send_confirmation_email(self):
        short_url = 'http://localhost:8000/s/abc123'
        with (
            patch('src.services.mail.aiosmtplib.send', new_callable=AsyncMock) as mock_send,
            patch.object(MailService, '_get_short_url', new_callable=AsyncMock) as mock_short,
        ):
            mock_short.return_value = short_url
            service = make_service()
            await service.send_confirmation_email(
                to='alice@example.com',
                username='alice',
                token='test-token-123',
            )
            mock_send.assert_awaited_once()
            msg = mock_send.call_args.args[0]
            assert msg['To'] == 'alice@example.com'
            body = msg.get_payload(decode=True).decode()
            assert short_url in body
            assert 'alice' in body

    async def test_send_confirmation_email_falls_back_on_link_service_error(self):
        with (
            patch('src.services.mail.aiosmtplib.send', new_callable=AsyncMock) as mock_send,
            patch.object(MailService, '_get_short_url', side_effect=Exception('link down')),
        ):
            service = make_service()
            await service.send_confirmation_email(
                to='alice@example.com',
                username='alice',
                token='test-token-123',
            )
            mock_send.assert_awaited_once()
            msg = mock_send.call_args.args[0]
            body = msg.get_payload(decode=True).decode()
            assert 'confirm?token=test-token-123' in body
