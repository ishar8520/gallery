from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='auth_superuser_')
    
    username: str
    password: str
    email: str
    
admin = AdminConfig()