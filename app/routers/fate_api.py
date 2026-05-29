from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import get_db
from app.models.uploaded_file import UploadedFile
from app.models.model_record import ModelRecord
from app.models.prediction_record import PredictionRecord
from app.models.job_record import JobRecord
from app.models.app_user import AppUser
from app.services.remote_fate_service import RemoteFateService
from app.dependencies.auth import get_current_user, get_fate_service
from app.schemas.fate import (
    JobQueryRequest,
    DataQueryRequest,
    DeleteTableRequest,
    OutputTableRequest,
    ModelQueryRequest,
    UploadDataRequest,
    PipelineRequest,
    TrainingCreateRequest,
    JobIdRequest,
    MetricsRequest,
    ModelUpdateRequest,
    ModelDetailRequest,
    PredictionCreateRequest,
    PredictionDetailRequest,
    PredictionUpdateRequest,
)


router = APIRouter(prefix="/api/fate", tags=["FATE API"])

# This interface is used to obtain all the datasets that can be used for training.
@router.get("/training/datasets")
def get_training_datasets(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.usage_type == "train") # Filtering only displays the files used for training.
        .order_by(UploadedFile.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "datasets": [
            {
                "id": f.id,
                "file_name": f.file_name,
                "description": f.description,
                "size_bytes": f.size_bytes,
                "namespace": f.namespace,
                "table_name": f.table_name,
                "created_at": f.created_at.strftime("%Y-%m-%d %H:%M:%S") if f.created_at else "-",
            }
            for f in files
        ],
    }

# This interface is used for creating training.
@router.post("/training/create")
def create_training(
    req: TrainingCreateRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    # First, query the uploaded files based on the dataset ID.
    file_obj = db.query(UploadedFile).filter(UploadedFile.id == req.dataset_file_id).first()
    if not file_obj:
        return {"success": False, "message": "Dataset file not found"}

    # The information required for converting WebApp data into FATE
    result = service.start_training_with_config(
        dataset_name=file_obj.table_name,
        dataset_namespace=file_obj.namespace,
        algorithm=req.algorithm,
        learning_rate=req.learning_rate,
        epochs=req.epochs,
        batch_size=req.batch_size,
        role=req.role,
        party_id=req.party_id,
    )

    # Extract the Job ID and model information from the training results.
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    combined = stdout + "\n" + stderr

    model_info = service.extract_model_info(stdout) if hasattr(service, "extract_model_info") else {}
    job_id = model_info.get("job_id") or result.get("job_id") or service.extract_job_id(combined)

    # Determine the model ID and version.
    fate_model_id = model_info.get("model_id") or job_id
    fate_model_version = model_info.get("model_version") or "v1.0"

    if result.get("success", False) and job_id:

        # If the job_id does not exist in the database, create a new record for the training task.
        existing_job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
        if not existing_job:
            job_record = JobRecord(
                job_id=job_id,
                job_type="Training",
                name=file_obj.file_name,
                role=req.role,
                party_id=req.party_id,
                status="SUBMITTED",
                source_script=req.algorithm,
            )
            db.add(job_record)

        # If the model has not been saved before, save a record of the model.
        existing_model = db.query(ModelRecord).filter(ModelRecord.model_id == fate_model_id).first()
        if not existing_model:
            pipeline_path = f"/data/projects/fate/examples/webapp_train_pipeline_{file_obj.table_name}.pkl"

            model_record = ModelRecord(
                model_id=fate_model_id,
                name=f"{req.algorithm}_{file_obj.file_name}",
                algorithm=req.algorithm,
                version=fate_model_version,

                # Save the information obtained from FATE.
                description=(
                    f"Generated from dataset {file_obj.file_name}; "
                    f"FATE table={file_obj.namespace}.{file_obj.table_name}; "
                    f"training_job_id={job_id}; "
                    f"pipeline_path={pipeline_path}"
                ),
            )
            db.add(model_record)

        db.commit()

    # Return the training results.
    return {
        "success": result.get("success", False),
        "job_id": job_id or result.get("job_id"),
        "model_id": fate_model_id if result.get("success", False) else None,
        "model_version": fate_model_version if result.get("success", False) else None,
        "stdout": stdout,
        "stderr": result.get("stderr", ""),
        "task_errors": result.get("task_errors"),
        "generated_script": result.get("generated_script"),
    }

# Query the training progress based on the Job ID.
@router.post("/training/progress")
def training_progress(
    req: JobIdRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.get_training_progress(req.job_id)

# Retrieve the training log text based on the Job ID.
@router.post("/training/logs")
def training_logs(
    req: JobIdRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.get_job_logs_text(req.job_id)

# This is used to query what metrics are output by the FATE task itself. However, similar to the above "progress" method, due to changes in the implementation, the function call has not been implemented for the time being.
@router.post("/training/metrics")
def training_metrics(
    req: MetricsRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.get_job_metrics(
        job_id=req.job_id,
        role=req.role,
        party_id=req.party_id,
        component_name=req.component_name,
    )

# Stop the running FATE Job.
@router.post("/training/stop")
def training_stop(
    req: JobIdRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.stop_job(req.job_id)

# Used to check whether the remote FATE environment is ready.
@router.get("/root-check")
def root_check(
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.ensure_environment_ready()

# Used for debugging pipeline components.
@router.get("/debug/components")
def debug_components(
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.list_pipeline_components()

# Used to check whether fate_flow_server.py is running.
@router.get("/status")
def check_fate_flow_status(
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.check_fate_flow_process()

# This interface is used for the summary display on the homepage Dashboard.
@router.get("/dashboard/main-summary")
def dashboard_main_summary(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    # Check if FATE is running.
    status_result = service.check_fate_flow_process()
    fate_running = status_result.get("running", False)

    # Update the status of the local JobRecord.
    records = db.query(JobRecord).order_by(JobRecord.created_at.desc()).all()
    for record in records:
        try:
            result = service.query_job_status_only(record.job_id)
            new_status = result.get("status", "UNKNOWN")
            if new_status:
                record.status = new_status
                record.updated_at = datetime.utcnow()
        except Exception:
            pass

    db.commit()

    records = db.query(JobRecord).order_by(JobRecord.created_at.desc()).limit(limit).all()
    all_records = db.query(JobRecord).all()

    # Count the number of statistical training and prediction tasks.
    train_count = sum(1 for r in all_records if r.job_type == "Training")
    predict_count = sum(1 for r in all_records if r.job_type == "Prediction")

    # Return to the recent task list.
    job_list = [
        {
            "job_id": r.job_id,
            "type": r.job_type,
            "status": r.status,
            "role": r.role,
            "party_id": r.party_id,
            "time": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "-",
        }
        for r in records
    ]

    return {
        "success": True,
        "fate_flow_running": fate_running,
        "fate_flow_message": "Connected" if fate_running else "Disconnected",
        "recent_train_job_number": train_count,
        "recent_predicted_number": predict_count,
        "job_list": job_list,
        "debug_status_stdout": status_result.get("stdout", ""),
        "debug_status_stderr": status_result.get("stderr", ""),
        "debug_status_message": status_result.get("message", ""),
    }

# Complete query of a specific FATE Job.
@router.post("/job/query")
def query_job(
    req: JobQueryRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.query_job(req.job_id, req.role, req.party_id)

# Simplified query, only transmitting job_id.
@router.get("/job/query/{job_id}")
def query_job_simple(
    job_id: str,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.query_job_simple(job_id)

# Obtain the log of a certain Job.
@router.get("/job/log/{job_id}")
def get_job_log(
    job_id: str,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.get_job_log(job_id)

# This interface is used for data tables.
@router.post("/output/table")
def query_output_table(
    req: OutputTableRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.query_output_table(req.job_id, req.role, req.party_id, req.table_name)

# Upload the data to FATE based on the JSON configuration file on the remote server.
@router.post("/data/upload")
def upload_data(
    req: UploadDataRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.upload_data(req.json_config_path)

# Query the upload history of FATE data.
@router.get("/data/history")
def upload_history(
    limit: int = 20,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.upload_history(limit)

# Query the FATE data table based on the namespace and name.
@router.post("/data/query")
def query_data(
    req: DataQueryRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.query_data(req.namespace, req.name)

# Download or preview the content of the FATE data table.
@router.get("/data/download")
def download_data_preview(
    namespace: str,
    name: str,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.download_data_preview(namespace, name)

# Delete the data tables in FATE.
@router.post("/table/delete")
def delete_table(
    req: DeleteTableRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.delete_table(req.namespace, req.table_name)

# For debugging purposes, directly run the specified training pipeline script.
@router.post("/training/start")
def start_training(
    req: PipelineRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    result = service.start_training(req.pipeline_script)
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    job_id = result.get("job_id") or service.extract_job_id(stdout + "\n" + stderr)

    if job_id:
        existing = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
        if not existing:
            record = JobRecord(
                job_id=job_id,
                job_type="Training",
                name=req.pipeline_script,
                role="guest",
                party_id="9999",
                status="SUBMITTED",
                source_script=req.pipeline_script,
            )
            db.add(record)
            db.commit()

    return {
        "success": result.get("success", False),
        "job_id": job_id,
        "stdout": stdout,
        "stderr": stderr,
    }

# Query details of the FATE model.
@router.post("/model/query")
def model_query(
    req: ModelQueryRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.model_query(req.model_id, req.model_version)

# Export the FATE model.
@router.post("/model/export")
def model_export(
    req: ModelQueryRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.model_export(req.model_id, req.model_version)

# Load the model.
@router.post("/model/load")
def model_load(
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.model_load()

# Obtain the prediction configuration file.
@router.post("/predict/conf")
def get_predict_conf(
    req: ModelQueryRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.get_predict_conf(req.model_id, req.model_version)

# Obtain the prediction DSL file.
@router.post("/predict/dsl")
def get_predict_dsl(
    req: ModelQueryRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.get_predict_dsl(req.model_id, req.model_version)

# For debugging purposes, directly run the specified prediction pipeline script.
@router.post("/prediction/start")
def start_prediction(
    req: PipelineRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    result = service.start_prediction(req.pipeline_script)
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    job_id = result.get("job_id") or service.extract_job_id(stdout + "\n" + stderr)

    if job_id:
        existing = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
        if not existing:
            record = JobRecord(
                job_id=job_id,
                job_type="Prediction",
                name=req.pipeline_script,
                role="guest",
                party_id="9999",
                status="SUBMITTED",
                source_script=req.pipeline_script,
            )
            db.add(record)
            db.commit()

    return {
        "success": result.get("success", False),
        "job_id": job_id,
        "stdout": stdout,
        "stderr": stderr,
    }


@router.get("/models/list")
def list_models(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Query the model records in the local database.
    models = db.query(ModelRecord).order_by(ModelRecord.created_at.desc()).all()

    return {
        "success": True,
        "models": [
            {
                "model_id": m.model_id,
                "name": m.name,
                "algorithm": m.algorithm,
                "version": m.version,
                "description": m.description,
                "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else "-",
            }
            for m in models
        ],
    }

# Query the detailed information of the corresponding model.
@router.post("/models/detail")
def model_detail(
    req: ModelDetailRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    local_model = db.query(ModelRecord).filter(ModelRecord.model_id == req.model_id).first()
    fate_result = service.model_query(req.model_id, req.version)

    return {
        "success": True,
        "local": {
            "model_id": local_model.model_id if local_model else req.model_id,
            "name": local_model.name if local_model else req.model_id,
            "algorithm": local_model.algorithm if local_model else "-",
            "version": local_model.version if local_model else req.version,
            "description": local_model.description if local_model else "",
        },
        "fate_stdout": fate_result.get("stdout", ""),
        "fate_stderr": fate_result.get("stderr", ""),
    }

# Used to update the local model records.
@router.put("/models/update")
def update_model(
    req: ModelUpdateRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    model = db.query(ModelRecord).filter(ModelRecord.model_id == req.model_id).first()
    if not model:
        return {"success": False, "message": "Model not found"}

    model.name = req.name
    model.version = req.version
    model.description = req.description
    db.commit()

    return {
        "success": True,
        "message": "Model updated successfully",
    }

# Extract the pipeline_path from the description, then delete the pipeline file on the server, and subsequently delete the ModelRecord in the database.
@router.delete("/models/{model_id}")
def delete_model(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    model = db.query(ModelRecord).filter(ModelRecord.model_id == model_id).first()
    if not model:
        return {"success": False, "message": "Model not found"}

    pipeline_path = service.extract_pipeline_path(model.description or "")
    server_delete_result = service.delete_model_files_from_server(pipeline_path)

    db.delete(model)
    db.commit()

    return {
        "success": True,
        "message": "Model record and server pipeline file deleted.",
        "pipeline_path": pipeline_path,
        "server_delete_stdout": server_delete_result.get("stdout", ""),
        "server_delete_stderr": server_delete_result.get("stderr", ""),
    }

# Return the list of models that can be used for prediction.
@router.get("/prediction/models")
def prediction_models(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    models = db.query(ModelRecord).order_by(ModelRecord.created_at.desc()).all()

    return {
        "success": True,
        "models": [
            {
                "model_id": m.model_id,
                "name": m.name,
                "version": m.version,
                "algorithm": m.algorithm,
            }
            for m in models
        ],
    }

# Return the dataset that can be used for prediction.
@router.get("/prediction/datasets")
def prediction_datasets(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.usage_type == "predict")
        .order_by(UploadedFile.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "datasets": [
            {
                "id": f.id,
                "file_name": f.file_name,
                "description": f.description,
                "size_bytes": f.size_bytes,
            }
            for f in files
        ],
    }

# Based on the model selected by the user and the prediction dataset, invoke FATE to initiate the prediction task. Once successful, save the PredictionRecord and obRecord.
@router.post("/prediction/create")
def create_prediction(
    req: PredictionCreateRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    # If the model does not exist, return failure directly.
    model = db.query(ModelRecord).filter(ModelRecord.model_id == req.model_id).first()
    if not model:
        return {"success": False, "message": "Model not found"}

    # If the dataset does not exist, return failure directly.
    dataset = db.query(UploadedFile).filter(UploadedFile.id == req.dataset_file_id).first()
    if not dataset:
        return {"success": False, "message": "Dataset not found"}

    # Extract pipeline_path.
    pipeline_path = service.extract_pipeline_path(model.description or "")
    if not pipeline_path:
        return {
            "success": False,
            "message": (
                "Model pipeline file path not found in MODEL_RECORDS.DESCRIPTION. "
                "Please retrain this model after updating the code."
            ),
        }

    # Invoke FATE to initiate the prediction.
    result = service.start_prediction_with_config(
        model_id=model.model_id,
        model_version=model.version,
        dataset_name=dataset.table_name,
        dataset_namespace=dataset.namespace,
        pipeline_path=pipeline_path,
    )

    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    job_id = result.get("job_id") or service.extract_job_id(stdout + "\n" + stderr)

    if result.get("success", False) and job_id:
        existing_pred = (
            db.query(PredictionRecord)
            .filter(PredictionRecord.prediction_job_id == job_id)
            .first()
        )
        if not existing_pred:
            # Save a history of one prediction in the prediction record table.
            pred_record = PredictionRecord(
                prediction_job_id=job_id,
                model_id=model.model_id,
                model_name=model.name,
                dataset_file_id=dataset.id,
                dataset_name=dataset.file_name,
                status="SUBMITTED",
                note="",
            )
            db.add(pred_record)

        existing_job = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
        if not existing_job:
            # Save a general task record, and the Dashboard and task list can also display the predictive tasks.
            job_record = JobRecord(
                job_id=job_id,
                job_type="Prediction",
                name=f"{model.name}->{dataset.file_name}",
                role=req.role,
                party_id=req.party_id,
                status="SUBMITTED",
                source_script="predict",
            )
            db.add(job_record)

        db.commit()

    return {
        "success": result.get("success", False),
        "job_id": job_id,
        "stdout": stdout,
        "stderr": result.get("stderr", ""),
        "task_errors": result.get("task_errors"),
        "generated_script": result.get("generated_script"),
    }

# This interface is used to view all the prediction records.
@router.get("/prediction/list")
def prediction_list(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    records = db.query(PredictionRecord).order_by(PredictionRecord.created_at.desc()).all()

    # Query the latest status of FATE and update the database.
    for record in records:
        try:
            result = service.get_prediction_progress(record.prediction_job_id)
            record.status = result.get("status", record.status)
            record.updated_at = datetime.utcnow()
        except Exception:
            pass

    db.commit()

    # Requery the database.
    records = db.query(PredictionRecord).order_by(PredictionRecord.created_at.desc()).all()

    # Return the final result.
    return {
        "success": True,
        "predictions": [
            {
                "prediction_job_id": r.prediction_job_id,
                "model_name": r.model_name,
                "dataset_name": r.dataset_name,
                "status": r.status,
                "time": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "-",
                "note": r.note or "",
            }
            for r in records
        ],
    }

# Query the status of a certain prediction task.
@router.post("/prediction/status")
def prediction_status(
    req: PredictionDetailRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.get_prediction_progress(req.prediction_job_id)

# Obtain the predicted result text.
@router.post("/prediction/result")
def prediction_result(
    req: PredictionDetailRequest,
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    return service.get_prediction_result_text(req.prediction_job_id)

# Used to update the remarks of the prediction record.
@router.put("/prediction/update")
def prediction_update(
    req: PredictionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    record = (
        db.query(PredictionRecord)
        .filter(PredictionRecord.prediction_job_id == req.prediction_job_id)
        .first()
    )

    if not record:
        return {"success": False, "message": "Prediction record not found"}

    record.note = req.note
    record.updated_at = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "Prediction record updated"}

# Delete the prediction record.
@router.delete("/prediction/{prediction_job_id}")
def delete_prediction(
    prediction_job_id: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    service: RemoteFateService = Depends(get_fate_service),
):
    # First, look for the prediction records.
    record = (
        db.query(PredictionRecord)
        .filter(PredictionRecord.prediction_job_id == prediction_job_id)
        .first()
    )

    if not record:
        return {"success": False, "message": "Prediction record not found"}

    # Then look for the corresponding dataset.
    dataset = db.query(UploadedFile).filter(UploadedFile.id == record.dataset_file_id).first()

    server_delete_result = {
        "success": True,
        "stdout": "No dataset found. Nothing deleted.",
        "stderr": "",
    }

    # After finding it, delete it.
    if dataset:
        server_delete_result = service.delete_prediction_files_from_server(dataset.table_name)

    db.delete(record)
    db.commit()

    return {
        "success": True,
        "message": "Prediction record and generated prediction script deleted.",
        "prediction_job_id": prediction_job_id,
        "server_delete_stdout": server_delete_result.get("stdout", ""),
        "server_delete_stderr": server_delete_result.get("stderr", ""),
    }