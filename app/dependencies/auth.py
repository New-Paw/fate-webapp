from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.app_user import AppUser
from app.services.auth_service import decode_access_token, decrypt_server_password
from app.services.remote_fate_service import RemoteFateService

# Obtain the currently logged-in user. If the user is not logged in or the token is invalid, directly return a 401 error.
def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> AppUser:
    token = request.cookies.get("access_token")

    # If the browser does not have an access_token, it indicates that the user has not logged in.
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Use the "decode_access_token" function to determine whether the token is valid.
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Extract the user ID from the payload and check whether it is valid.
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Query the database based on the user ID.
    user = db.query(AppUser).filter(AppUser.id == int(user_id)).first()

    # Also determine whether the user exists or whether it is enabled.
    if not user or user.is_active != 1:
        raise HTTPException(status_code=401, detail="User disabled or not found")

    return user

# Similar to the get_current_user method, but if the condition is met, it will go back to the login interface. Used for the HTML page.
def get_current_user_or_redirect(
    request: Request,
    db: Session = Depends(get_db)
) -> AppUser:
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=307, headers={"Location": "/login"})

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=307, headers={"Location": "/login"})

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=307, headers={"Location": "/login"})

    user = db.query(AppUser).filter(AppUser.id == int(user_id)).first()

    if not user or user.is_active != 1:
        raise HTTPException(status_code=307, headers={"Location": "/login"})

    return user

# Based on the server account and password of the currently logged-in user, create a RemoteFateService object to establish a connection with the remote FATE server.
def get_fate_service(
    current_user: AppUser = Depends(get_current_user)
) -> RemoteFateService:
    server_password = decrypt_server_password(current_user.server_password_encrypted)

    return RemoteFateService(
        server_username=current_user.server_username,
        server_password=server_password
    )