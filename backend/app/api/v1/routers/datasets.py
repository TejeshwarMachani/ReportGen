import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.models.dataset import Dataset
from app.services.dataset_service import DatasetService
from app.auth import get_current_user
from pydantic import BaseModel
from typing import Optional, List


router = APIRouter(prefix="/datasets", tags=["datasets"])


class DatasetResponse(BaseModel):
    id: str
    name: str
    source_type: str
    schema_json: Optional[dict]
    row_count: int
    status: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a CSV or Excel file and start async parsing"""
    org_id = current_user.org_id

    # Use provided name or derive from filename
    file_name = file.filename or "upload"
    dataset_name = name or file_name.replace(".csv", "").replace(".xlsx", "")

    # Create dataset record
    dataset = await DatasetService.create_dataset(
        db=db,
        org_id=org_id,
        uploaded_by=current_user.id,
        file=file,
        name=dataset_name,
    )

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        source_type=dataset.source_type,
        schema_json=json.loads(dataset.schema_json) if dataset.schema_json else None,
        row_count=dataset.row_count,
        status=dataset.status,
        created_at=dataset.created_at.isoformat() if dataset.created_at else "",
    )


@router.get("", response_model=List[DatasetResponse])
async def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List datasets for current org"""
    datasets = db.query(Dataset).filter(Dataset.org_id == current_user.org_id).all()
    return [
        DatasetResponse(
            id=d.id,
            name=d.name,
            source_type=d.source_type,
            schema_json=json.loads(d.schema_json) if d.schema_json else None,
            row_count=d.row_count,
            status=d.status,
            created_at=d.created_at.isoformat() if d.created_at else "",
        )
        for d in datasets
    ]


@router.get("/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dataset detail"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        source_type=dataset.source_type,
        schema_json=json.loads(dataset.schema_json) if dataset.schema_json else None,
        row_count=dataset.row_count,
        status=dataset.status,
        created_at=dataset.created_at.isoformat() if dataset.created_at else "",
    )


@router.get("/{dataset_id}/preview")
async def get_dataset_preview(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get first ~50 rows preview of dataset"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # In real implementation, would read from Min/S3
    # For now, return placeholder
    return {
        "dataset_id": dataset_id,
        "preview_rows": 0,
        "schema": json.loads(dataset.schema_json) if dataset.schema_json else [],
        "message": "Preview would be generated from stored file",
    }


@router.patch("/{dataset_id}")
async def update_dataset(
    dataset_id: str,
    name: Optional[str] = None,
    column_type_overrides: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update dataset name or column type overrides"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if name:
        dataset.name = name
    if column_type_overrides:
        # Apply overrides to schema
        if dataset.schema_json:
            schema = json.loads(dataset.schema_json)
            for override in column_type_overrides.get("overrides", []):
                for col in schema:
                    if col["column"] == override.get("column"):
                        col["inferred_type"] = override.get("type")

            dataset.schema_json = json.dumps(schema)

    db.commit()
    db.refresh(dataset)

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        source_type=dataset.source_type,
        schema_json=json.loads(dataset.schema_json) if dataset.schema_json else None,
        row_count=dataset.row_count,
        status=dataset.status,
        created_at=dataset.created_at.isoformat() if dataset.created_at else "",
    )


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
):
    """Soft-delete a dataset (mark as error status)"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset.status = "error"
    dataset.error_message = "Dataset soft-deleted"
    db.commit()

    return {"detail": "Dataset marked as deleted"}