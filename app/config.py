from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseModel):
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # The database automatically reads DATABASE_URL.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "oracle+oracledb://xjiangp00:usIXPHCk@gort.fit.vutbr.cz:1521/?service_name=orclpdb"
    )

    # SSH connection to the college server.
    GRACE_HOST: str = os.getenv("GRACE_HOST", "grace1.fit.vutbr.cz")
    GRACE_PORT: int = int(os.getenv("GRACE_PORT", "22"))
    GRACE_USER: str = os.getenv("GRACE_USER", "")
    GRACE_PASSWORD: str = os.getenv("GRACE_PASSWORD", "")

    # Docker container.
    FATE_CONTAINER: str = os.getenv("FATE_CONTAINER", "standalone_fate")

    # The FATE root directory inside the container.
    FATE_ROOT: str = os.getenv("FATE_ROOT", "/data/projects/fate")

    # Login / Register - Authentication Configuration.
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "dev-secret-change-me")
    APP_FERNET_KEY: str = os.getenv("APP_FERNET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))


settings = Settings()