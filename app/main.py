from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Database
from app.db import Base, engine

# Routers
from app.routers import auth
from app.routers import pages
from app.routers import fate_api
from app.routers.file_storage import router as file_storage_router

# Models
from app.models.app_user import AppUser
from app.models.uploaded_file import UploadedFile
from app.models.job_record import JobRecord
from app.models.model_record import ModelRecord
from app.models.prediction_record import PredictionRecord


app = FastAPI(title="FATE WebApp UI")

# Automatically create database tables.
Base.metadata.create_all(bind=engine)

# Static files.
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Authentication routes.
app.include_router(auth.router)

# Page routing.
app.include_router(pages.router)

# API routing.
app.include_router(fate_api.router)
app.include_router(file_storage_router)