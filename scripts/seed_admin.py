from pathlib import Path
import sys

# Add project root directory to Python import path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.db import Base, engine, SessionLocal

# Import all the models.
from app.models.app_user import AppUser
from app.models.uploaded_file import UploadedFile
from app.models.job_record import JobRecord
from app.models.model_record import ModelRecord
from app.models.prediction_record import PredictionRecord

from app.config import settings
from app.services.auth_service import hash_password, encrypt_server_password

def main():

    print("Initializing database tables...")

    # Automatically create tables based on the SQLAlchemy model.
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print(f"Checking administrator account: {settings.ADMIN_ACCOUNT}")

        existing_user = (
            db.query(AppUser)
            .filter(AppUser.account == settings.ADMIN_ACCOUNT)
            .first()
        )

        if existing_user:
            print(
                f"Administrator account already exists: "
                f"{settings.ADMIN_ACCOUNT}"
            )
            print("No changes were made.")
            return

        # Check whether the account and password for the remote FATE server have been configured.
        if not settings.ADMIN_SERVER_USERNAME.strip():
            raise RuntimeError(
                "ADMIN_SERVER_USERNAME is empty. "
                "Please set it in your local .env file."
            )

        if not settings.ADMIN_SERVER_PASSWORD.strip():
            raise RuntimeError(
                "ADMIN_SERVER_PASSWORD is empty. "
                "Please set it in your local .env file."
            )

        if not settings.APP_FERNET_KEY.strip():
            raise RuntimeError(
                "APP_FERNET_KEY is empty. "
                "Please generate and set it in your local .env file."
            )

        print("Creating administrator account...")

        admin_user = AppUser(
            account=settings.ADMIN_ACCOUNT,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            server_username=settings.ADMIN_SERVER_USERNAME,

            # The password for the remote server needs to be used for subsequent SSH connections, so it is encrypted and saved.
            server_password_encrypted=encrypt_server_password(
                settings.ADMIN_SERVER_PASSWORD
            ),

            is_active=1,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("Administrator account created successfully.")
        print("--------------------------------------------")
        print(f"Account : {settings.ADMIN_ACCOUNT}")
        print(f"Password: {settings.ADMIN_PASSWORD}")
        print("--------------------------------------------")
        print("Remote server password has been encrypted in database.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()