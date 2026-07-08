import json
import logging
import re
import uuid
from typing import Annotated
from uuid import UUID

import bcrypt
from aiokafka import AIOKafkaProducer
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.models.registration import RequestRegistration
from src.api.v1.models.user import RequestChangePassword, RequestPatchUser, ResponseUser, ResponseUserAdmin
from src.core.config import settings
from src.dependences.postgres import PostgresDep, get_async_postgres
from src.dependences.redis import RedisDep, get_async_redis
from src.kafka.events import email_confirmation_requested_event
from src.kafka.producer import get_kafka_producer
from src.models.enums import Roles
from src.models.user import User, UserRoles
from src.services import exceptions

logger = logging.getLogger(__name__)

MAIL_TOPIC = 'mail-events'


class UserService:
    pg_session: PostgresDep
    redis_session: RedisDep
    kafka: AIOKafkaProducer | None

    def __init__(
        self,
        postgres: AsyncSession,
        redis: RedisDep,
        kafka_producer: AIOKafkaProducer | None = None,
    ) -> None:
        self.pg_session = postgres
        self.redis_session = redis
        self.kafka = kafka_producer

    async def get_register(self, request_model: RequestRegistration) -> None:
        """Регистрация: резервирует данные в Redis, отправляет письмо с подтверждением."""
        if not self.is_valid_email(request_model.email):
            raise exceptions.BadEmailException

        # Проверяем подтверждённых пользователей в БД
        if await self.pg_session.get_user_by_username(request_model.username):
            raise exceptions.UsernameExistException
        if await self.pg_session.get_user_by_email(request_model.email):
            raise exceptions.EmailExistException

        # Атомарно резервируем в Redis — защита от race condition
        ttl = settings.registration.ttl_seconds
        if not await self.redis_session.set_nx(
            f'reserve:username:{request_model.username}', '1', ttl
        ):
            raise exceptions.UsernameExistException
        if not await self.redis_session.set_nx(
            f'reserve:email:{request_model.email}', '1', ttl
        ):
            await self.redis_session.drop_value(f'reserve:username:{request_model.username}')
            raise exceptions.EmailExistException

        token = str(uuid.uuid4())
        password = request_model.password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password, salt).decode('utf-8')

        pending_data = json.dumps({
            'username': request_model.username,
            'password_hash': password_hash,
            'email': request_model.email,
        })
        await self.redis_session.set_value(f'pending:{token}', pending_data, ttl)

        if self.kafka:
            try:
                await self.kafka.send_and_wait(
                    MAIL_TOPIC,
                    email_confirmation_requested_event(
                        token, request_model.username, request_model.email
                    ),
                )
            except Exception:
                logger.exception('Failed to send email_confirmation_requested event to Kafka')

    async def confirm_registration(self, token: str) -> UUID:
        """Подтверждение email: читает данные из Redis и создаёт пользователя в БД."""
        raw = await self.redis_session.get_value(f'pending:{token}')
        if raw is None:
            raise exceptions.ConfirmationTokenExpiredException

        data = json.loads(raw)
        username = data['username']
        email = data['email']
        password_hash = data['password_hash']

        role = await self.pg_session.get_role(Roles.USER)
        user = User(username=username, password=password_hash, email=email)
        user_role = UserRoles(user=user, role=role)
        user_id = await self.pg_session.add_user(user)
        await self.pg_session.add_user_role(user_role)

        await self.redis_session.drop_value(f'pending:{token}')
        await self.redis_session.drop_value(f'reserve:username:{username}')
        await self.redis_session.drop_value(f'reserve:email:{email}')

        return user_id

    async def get_user(self, user_id: UUID) -> ResponseUser:
        """Получение данных из БД о пользователе"""
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotFoundException
        return ResponseUser(
            user_id=user.id,
            username=user.username,
            email=user.email)

    async def delete_user(self, user_id: UUID) -> None:
        """Удаление пользователя из БД"""
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotFoundException
        return await self.pg_session.delete_user(user_id)

    async def patch_user(self, user_id: UUID, user_update: RequestPatchUser) -> UUID:
        """Обновление данные о пользователе в БД"""
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotFoundException
        await self.check_exist_user(current_user=user, update_user=user_update)
        if user_update.username not in [user.username, None]:
            user.username = user_update.username
        if user_update.email not in [user.email, None]:
            user.email = user_update.email
        return await self.pg_session.add_user(user)

    async def get_all_users(self) -> list[ResponseUserAdmin]:
        """Получение списка всех пользователей с ролями (только для ADMIN)"""
        users = await self.pg_session.get_all_users()
        result = []
        for user in users:
            roles = [ur.role.role.value for ur in user.user_roles]
            result.append(ResponseUserAdmin(
                user_id=user.id,
                username=user.username,
                email=user.email,
                roles=roles,
            ))
        return result

    async def change_password(
        self, user_id: UUID, request: RequestChangePassword
    ) -> None:
        """Смена пароля: проверяет текущий пароль, хэширует и сохраняет новый"""
        user = await self.pg_session.get_user_by_id(user_id)
        if not user:
            raise exceptions.UserNotFoundException
        if not bcrypt.checkpw(request.current_password.encode('utf-8'), user.password.encode('utf-8')):
            raise exceptions.BadCredsException
        salt = bcrypt.gensalt()
        user.password = bcrypt.hashpw(request.new_password.encode('utf-8'), salt).decode('utf-8')
        await self.pg_session.add_user(user)

    async def check_exist_user(self, current_user: User, update_user: RequestPatchUser) -> bool:
        """Проверка существания пользователя в БД"""
        for field, value in update_user:
            if field == 'username' and value != current_user.username:
                user = await self.pg_session.get_user_by_username(value)
                if user:
                    raise exceptions.UsernameExistException
            elif field == 'email' and value != current_user.email:
                email = await self.pg_session.get_user_by_email(value)
                if email:
                    raise exceptions.EmailExistException
        return True

    def is_valid_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.fullmatch(pattern, email))


def get_user_service(
    pg_dep: Annotated[AsyncSession, Depends(get_async_postgres)],
    redis_dep: Annotated[RedisDep, Depends(get_async_redis)],
    kafka: Annotated[AIOKafkaProducer, Depends(get_kafka_producer)],
) -> UserService:
    return UserService(postgres=pg_dep, redis=redis_dep, kafka_producer=kafka)
