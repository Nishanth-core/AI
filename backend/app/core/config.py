from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = Field("development", env="NODE_ENV")
    frontend_url: AnyHttpUrl = Field("http://localhost:5173", env="FRONTEND_URL")
    port: int = Field(8000, env="PORT")

    supabase_url: AnyHttpUrl = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")

    secret_key: str = Field("supersecretkey", env="SECRET_KEY")
    jwt_secret: str = Field("supersecretkey", env="JWT_SECRET")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(15, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
