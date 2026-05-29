from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.app_user import AppUser
from app.services.auth_service import (
    hash_password,
    verify_password,
    encrypt_server_password,
    create_access_token,
)

# Routing and template initialization.
router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="app/templates")

# This function handles the user's access to the login page.
@router.get("/login")
def login_page(request: Request):
    context = {
        "request": request,
        "page_title": "Login",
        "error": "",
        "current_user": None,
    }
    return templates.TemplateResponse(request, "login.html", context)

# This function handles the submission of the login form. When the user enters the account and password in login.html and clicks the login button, a POST request will be sent to /login.
@router.post("/login")
def login_submit(
    request: Request,
    account: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Based on the account input by the user, search for the user in the APP_USERS table.
    user = db.query(AppUser).filter(AppUser.account == account).first()

    # Check whether the user exists and whether the password is correct.
    if not user or not verify_password(password, user.password_hash):
        context = {
            "request": request,
            "page_title": "Login",
            "error": "Account or password is incorrect.",
            "current_user": None,
        }
        # When the login fails, return to the login page.
        return templates.TemplateResponse(
            request,
            "login.html",
            context,
            status_code=400
        )

    # If the user exists and the password verification is successful, a login token will be generated.
    token = create_access_token(user.id, user.account)

    # After successful login, the page will redirect to the home page.
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 12,
    )
    return response

# This function is used to handle user access to the registration page.
@router.get("/register")
def register_page(request: Request):
    context = {
        "request": request,
        "page_title": "Register",
        "error": "",
        "current_user": None,
    }
    return templates.TemplateResponse(request, "register.html", context)

# This function is used to handle the process of users registering for new accounts.
@router.post("/register")
def register_submit(
    request: Request,
    account: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    server_username: str = Form(...),
    server_password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Used to check whether the user's input is consistent in two instances.
    if password != confirm_password:
        context = {
            "request": request,
            "page_title": "Register",
            "error": "The two passwords are different.",
            "current_user": None,
        }
        return templates.TemplateResponse(
            request,
            "register.html",
            context,
            status_code=400
        )

    # Check whether the account already exists.
    existing = db.query(AppUser).filter(AppUser.account == account).first()
    if existing:
        context = {
            "request": request,
            "page_title": "Register",
            "error": "This account already exists.",
            "current_user": None,
        }
        # If it already exists, return an error: This account already exists. And the registration page is displayed again.
        return templates.TemplateResponse(
            request,
            "register.html",
            context,
            status_code=400
        )

    # Create a new AppUser user object.
    user = AppUser(
        account=account,
        password_hash=hash_password(password),
        server_username=server_username,
        server_password_encrypted=encrypt_server_password(server_password),
        is_active=1     # User status enabled.
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # After successful registration, log in directly.
    token = create_access_token(user.id, user.account)

    # After successful registration, you will be redirected to the home page.
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 12, # After successful registration, the browser will also retain the login status for 12 hours.
    )
    return response

# This function handles the logout process.
@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)  # After logging out, it will redirect to the login page.
    response.delete_cookie("access_token")
    return response