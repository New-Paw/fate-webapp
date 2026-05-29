from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates

from app.dependencies.auth import get_current_user_or_redirect
from app.models.app_user import AppUser


# Initialize the router and template renderer.
# This file is responsible only for returning HTML pages.
# Real data should be loaded dynamically by frontend JavaScript through API routes.
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Main dashboard page.
@router.get("/")
async def mainpage(
    request: Request,
    current_user: AppUser = Depends(get_current_user_or_redirect)
):
    context = {
        "request": request,
        "page_title": "Main Page",
        "current_user": current_user,

        # Default placeholders.
        # These values should be replaced by data from /api/fate/dashboard/main-summary.
        "fate_flow_state": "Unknown",
        "recent_train_job_number": 0,
        "recent_predicted_number": 0,
        "job_list": [],
    }

    return templates.TemplateResponse(
        request,
        "mainpage.html",
        context
    )

# Dataset management page.
@router.get("/data")
async def datapage(
    request: Request,
    current_user: AppUser = Depends(get_current_user_or_redirect)
):
    context = {
        "request": request,
        "page_title": "Data Page",
        "current_user": current_user,
    }

    return templates.TemplateResponse(
        request,
        "datapage.html",
        context
    )

# Training management page.
@router.get("/training")
async def trainingpage(
    request: Request,
    current_user: AppUser = Depends(get_current_user_or_redirect)
):
    context = {
        "request": request,
        "page_title": "Training Page",
        "current_user": current_user,

        # Default placeholders.
        # These should be replaced by API responses in app.js.
        "datasets": [],
        "algorithms": [],
        "progress": 0,
        "logs": [],
        "metrics": {},
    }

    return templates.TemplateResponse(
        request,
        "trainingpage.html",
        context
    )

# Model management page.
@router.get("/model")
async def modelpage(
    request: Request,
    current_user: AppUser = Depends(get_current_user_or_redirect)
):
    context = {
        "request": request,
        "page_title": "Model Page",
        "current_user": current_user,

        # Default placeholder.
        # Real model records should come from /api/fate/models/list.
        "models": [],
    }

    return templates.TemplateResponse(
        request,
        "modelpage.html",
        context
    )

# Prediction page.
@router.get("/predicted")
async def predictedpage(
    request: Request,
    current_user: AppUser = Depends(get_current_user_or_redirect)
):
    context = {
        "request": request,
        "page_title": "Predicted Page",
        "current_user": current_user,

        # Default placeholders.
        # Real data should come from prediction-related API routes.
        "models": [],
        "datasets": [],
        "predicted_list": [],
    }

    return templates.TemplateResponse(
        request,
        "predictedpage.html",
        context
    )