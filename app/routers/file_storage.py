from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime
import os

from app.db import get_db
from app.models.uploaded_file import UploadedFile
from app.models.app_user import AppUser
from app.services.remote_fate_service import RemoteFateService
from app.dependencies.auth import get_current_user, get_fate_service


router = APIRouter(prefix="/api/files", tags=["File Storage"])

# This function is used to generate the namespace of FATE based on the file's purpose.
def build_namespace(usage_type: str) -> str:
    if usage_type == "predict":
        return "projectA_predict_data"
    return "projectA_train_data"

# This function is used to generate the "table_name" of FATE.
def build_table_name(file_name: str, file_id_hint: int | None = None) -> str:
    base = os.path.splitext(file_name)[0].replace(" ", "_").replace("-", "_")
    if file_id_hint:
        return f"{base}_{file_id_hint}"
    return f"{base}_{int(datetime.utcnow().timestamp())}"

# Upload File Interface.
@router.post("/upload")
async def upload_file_to_db(
    file: UploadFile = File(...),
    description: str = Form(""),
    usage_type: str = Form("train"),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    fate_service: RemoteFateService = Depends(get_fate_service),
):
    # Prevent illegal input from being sent to the front end.
    if usage_type not in ("train", "predict"):
        raise HTTPException(status_code=400, detail="usage_type must be train or predict")

    # Read the content of the file.
    file_bytes = await file.read()
    namespace = build_namespace(usage_type)
    temp_table_name = build_table_name(file.filename)

    # Create database file records.
    new_file = UploadedFile(
        file_name=file.filename,
        content_type=file.content_type,
        size_bytes=len(file_bytes),
        usage_type=usage_type,
        namespace=namespace,
        table_name=temp_table_name,
        description=description,
        file_data=file_bytes,
    )

    # Write the file records into the database.
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    # Recreate the "table_name" using the real ID.
    real_table_name = build_table_name(file.filename, new_file.id)
    new_file.table_name = real_table_name
    db.commit()
    db.refresh(new_file)

    # The backend will write the uploaded files to this path on the remote server.
    remote_file_path = f"/data/projects/fate/examples/webapp_upload_{new_file.id}_{file.filename}"

    # Write to the temporary file on the remote server.
    write_result = fate_service.write_temp_dataset_file(remote_file_path, file_bytes)

    # If the file fails to be successfully written to the remote server, attempt to delete any remaining files on the server, delete the database record of UploadedFile and return a 500 error.
    if not write_result.get("success", False):
        try:
            fate_service.delete_dataset_files_from_server(
                file_id=new_file.id,
                file_name=new_file.file_name,
                table_name=new_file.table_name,
            )
        except Exception:
            pass

        db.delete(new_file)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                write_result.get("stderr")
                or write_result.get("stdout")
                or "Failed to write temp dataset file"
            ),
        )

    # Upload data to FATE.
    upload_result = fate_service.upload_dataset_to_fate(
        remote_file_path=remote_file_path,
        namespace=new_file.namespace,
        table_name=new_file.table_name,
        has_header=1,
        usage_type=new_file.usage_type,
        partitions=4,
        id_name="id",
        label_name="label",
    )

    # If the import of FATE fails, delete the server files, delete the database record of UploadedFile and return a 500 error.
    if not upload_result.get("success", False):
        try:
            fate_service.delete_dataset_files_from_server(
                file_id=new_file.id,
                file_name=new_file.file_name,
                table_name=new_file.table_name,
            )
        except Exception:
            pass

        db.delete(new_file)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=upload_result.get("stderr") or upload_result.get("stdout") or "FATE upload failed",
        )

    # Upload successful - Return result.
    return {
        "success": True,
        "message": "File saved into Oracle and uploaded to FATE successfully.",
        "file_id": new_file.id,
        "file_name": new_file.file_name,
        "size_bytes": new_file.size_bytes,
        "usage_type": new_file.usage_type,
        "namespace": new_file.namespace,
        "table_name": new_file.table_name,
        "fate_stdout": upload_result.get("stdout", ""),
    }

# This interface is used to query the list of uploaded files.
@router.get("/list")
def list_files(
    usage_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Query files from the "uploaded_files" table. 
    # Filter by "usage_type". 
    # Sort by creation time in descending order.
    query = db.query(UploadedFile)

    if usage_type in ("train", "predict"):
        query = query.filter(UploadedFile.usage_type == usage_type)

    files = query.order_by(UploadedFile.created_at.desc()).all()

    return {
        "success": True,
        "count": len(files),
        "files": [
            {
                "id": f.id,
                "file_name": f.file_name,
                "content_type": f.content_type,
                "size_bytes": f.size_bytes,
                "usage_type": f.usage_type,
                "namespace": f.namespace,
                "table_name": f.table_name,
                "description": f.description,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            }
            for f in files
        ],
    }

# This interface is used to view the details of a specific file.
@router.get("/{file_id}")
def get_file_detail(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    fate_service: RemoteFateService = Depends(get_fate_service),
):
    # If the file ID does not exist in the database, return 404.
    file_obj = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    # This step will query the metadata of this data table from FATE.
    meta = fate_service.query_dataset_meta(file_obj.namespace, file_obj.table_name)

    return {
        "success": True,
        "file": {
            "id": file_obj.id,
            "file_name": file_obj.file_name,
            "content_type": file_obj.content_type,
            "size_bytes": file_obj.size_bytes,
            "usage_type": file_obj.usage_type,
            "namespace": file_obj.namespace,
            "table_name": file_obj.table_name,
            "description": file_obj.description,
            "created_at": file_obj.created_at.isoformat() if file_obj.created_at else None,
            "updated_at": file_obj.updated_at.isoformat() if file_obj.updated_at else None,
        },
        # It can be seen whether there is indeed a corresponding table for FATE.
        "fate_meta_stdout": meta.get("stdout", ""),
        "fate_meta_stderr": meta.get("stderr", ""),
    }

# This interface is used to modify the file description.
@router.put("/{file_id}")
async def update_file(
    file_id: int,
    description: str = Form(""),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # If the corresponding file cannot be found, a 404 error will be returned.
    file_obj = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    # Update description and update time
    file_obj.description = description
    file_obj.updated_at = datetime.utcnow()

    # Submit the database.
    db.commit()
    db.refresh(file_obj)

    return {
        "success": True,
        "message": "File description updated successfully.",
        "file": {
            "id": file_obj.id,
            "file_name": file_obj.file_name,
            "usage_type": file_obj.usage_type,
            "namespace": file_obj.namespace,
            "table_name": file_obj.table_name,
            "description": file_obj.description,
            "updated_at": file_obj.updated_at.isoformat() if file_obj.updated_at else None,
        },
    }

# This interface is used to download the original uploaded files from the database.
@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # If the file does not exist, return 404.
    file_obj = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    # Return the file stream.
    return StreamingResponse(
        BytesIO(file_obj.file_data),
        media_type=file_obj.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_obj.file_name}"'},
    )

# Delete the files in the database and on the server side.
@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    fate_service: RemoteFateService = Depends(get_fate_service),
):
    # Query the database records. If no record is found, return 404.
    file_obj = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")

    # Save the deleted information.
    namespace = file_obj.namespace
    table_name = file_obj.table_name
    file_name = file_obj.file_name

    # Delete the FATE data table.
    fate_delete_result = fate_service.delete_dataset_from_fate(namespace, table_name)

    # Delete server files.
    server_file_delete_result = fate_service.delete_dataset_files_from_server(
        file_id=file_obj.id,
        file_name=file_name,
        table_name=table_name,
    )

    # Delete database records.
    db.delete(file_obj)
    db.commit()

    # Return the deletion result.
    return {
        "success": True,
        "message": f"File {file_id} deleted from Oracle, FATE table, and server files.",
        "fate_delete_stdout": fate_delete_result.get("stdout", ""),
        "fate_delete_stderr": fate_delete_result.get("stderr", ""),
        "server_file_delete_stdout": server_file_delete_result.get("stdout", ""),
        "server_file_delete_stderr": server_file_delete_result.get("stderr", ""),
    }

# This interface is used to clean up the "orphan files" on the remote server. Because the files that were deleted earlier had not been synchronized to the remote server.
@router.post("/cleanup-orphans")
def cleanup_orphan_server_files(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
    fate_service: RemoteFateService = Depends(get_fate_service),
):
    files = db.query(UploadedFile).all()
    active_ids = [f.id for f in files]

    result = fate_service.cleanup_orphan_webapp_files(active_ids)

    return {
        "success": result.get("success", False),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
    }