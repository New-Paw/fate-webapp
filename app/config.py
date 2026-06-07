from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()


class Settings(BaseModel):

    # FastAPI App Configuration
    APP_HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "oracle+oracledb://FATE_APP:fate_app_password@127.0.0.1:1521/?service_name=XEPDB1"
    )

    # Remote FATE Server SSH Configuration
    GRACE_HOST: str = os.getenv("GRACE_HOST", "")
    GRACE_PORT: int = int(os.getenv("GRACE_PORT", "22"))

    GRACE_USER: str = os.getenv("GRACE_USER", "")
    GRACE_PASSWORD: str = os.getenv("GRACE_PASSWORD", "")

    # FATE Docker Configuration
    FATE_CONTAINER: str = os.getenv("FATE_CONTAINER", "standalone_fate")
    FATE_ROOT: str = os.getenv("FATE_ROOT", "/data/projects/fate")


    # Optional FATE Flow SDK Configuration
    FATE_HOST: str = os.getenv("FATE_HOST", "127.0.0.1")
    FATE_PORT: int = int(os.getenv("FATE_PORT", "9380"))
    FATE_API_VERSION: str = os.getenv("FATE_API_VERSION", "v1")


    # Login / Register - Authentication Configuration
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "dev-secret-change-me")

    # APP_FERNET_KEY is used for encrypting / decrypting the password of the remote server.
    APP_FERNET_KEY: str = os.getenv("APP_FERNET_KEY", "")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720")
    )

    # Default Administrator Seed Configuration
    ADMIN_ACCOUNT: str = os.getenv("ADMIN_ACCOUNT", "administrator")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "123456")

    ADMIN_SERVER_USERNAME: str = os.getenv("ADMIN_SERVER_USERNAME", "")
    ADMIN_SERVER_PASSWORD: str = os.getenv("ADMIN_SERVER_PASSWORD", "")

settings = Settings()