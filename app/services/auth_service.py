from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from app.config import settings


# Create a password hashing tool.
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

# This function is used to perform hashing on the WebApp login password during the registration process.
def hash_password(raw_password: str) -> str:
    if raw_password is None:
        raise ValueError("Password cannot be empty")

    raw_password = str(raw_password)

    if len(raw_password.strip()) == 0:
        raise ValueError("Password cannot be empty")

    return pwd_context.hash(raw_password)

# This function is used to verify whether the password entered by the user during login is correct.
def verify_password(raw_password: str, password_hash: str) -> bool:
    if raw_password is None or not password_hash:
        return False

    try:
        return pwd_context.verify(str(raw_password), password_hash)
    except Exception:
        return False

# This function is used to create a Fernet encryptor.
def get_fernet() -> Fernet:
    if not settings.APP_FERNET_KEY:
        raise RuntimeError("APP_FERNET_KEY is not configured in .env")

    return Fernet(settings.APP_FERNET_KEY.encode("utf-8"))

# This function is used to encrypt the password of the remote server during the registration process.
def encrypt_server_password(raw_password: str) -> str:
    if raw_password is None:
        raise ValueError("Server password cannot be empty")
    
    f = get_fernet()

    return f.encrypt(str(raw_password).encode("utf-8")).decode("utf-8")

# This function is used to decrypt the server password before using the remote FATE service.
def decrypt_server_password(encrypted_password: str) -> str:
    f = get_fernet()
    return f.decrypt(encrypted_password.encode("utf-8")).decode("utf-8")

# This function is used to create an access token "token" after a successful login or registration.
def create_access_token(user_id: int, account: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "account": account,
        "exp": expire,
    }

    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm="HS256")

# This function is used to parse and validate the access_token.
def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.APP_SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return None