import pandas as pd
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.organization import Organization
from ..models.user import User
from ..models.dataset import Dataset


class DatasetService:
    """Service for handling dataset upload, parsing, and management"""

    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB limit
    ACCEPTED_TYPES = ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]

    @staticmethod
    def detect_column_types(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect inferred column types for a DataFrame"""
        schema = []
        for col in df.columns:
            series = df[col]
            # Determine inferred type
            if series.dtype == 'object':
                # Check if it looks like a date
                try:
                    pd.to_datetime(series.head(10), errors='raise')
                    inferred_type = "date"
                except:
                    # Check ratio of unique values to total
                    null_pct = series.isnull().sum() / len(series) * 100 if len(series) > 0 else 0
                    unique_pct = series.nunique() / len(series) * 100 if len(series) > 0 else 0
                    if unique_pct > 80:
                        inferred_type = "text"
                    elif unique_pct < 10:
                        inferred_type = "categorical"
                    else:
                        inferred_type = "text"
            elif pd.api.types.is_numeric_dtype(series):
                inferred_type = "number"
            elif pd.api.types.is_datetime64_any_dtype(series):
                inferred_type = "date"
            else:
                inferred_type = "text"

            schema.append({
                "column": col,
                "inferred_type": inferred_type,
                "nullable_pct": round(series.isnull().sum() / len(series) * 100, 2) if len(series) > 0 else 0
            })
        return schema

    @staticmethod
    def validate_file(file: UploadFile) -> tuple:
        """Validate uploaded file type and size"""
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > DatasetService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {DatasetService.MAX_FILE_SIZE // (1024*1024)}MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )

        # Check content type
        content_type = file.content_type or "unknown"
        if content_type not in DatasetService.ACCEPTED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {content_type}. Accepted: CSV, XLSX"
            )

        return file_size

    @staticmethod
    async def parse_file(file: UploadFile) -> tuple:
        """Parse CSV or Excel file into DataFrame and schema"""
        DatasetService.validate_file(file)

        file.file.seek(0)
        filename = file.filename.lower()

        if filename.endswith('.csv'):
            df = pd.read_csv(file.file, dtype=str, keep_default_na=False)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(file.file, dtype=str, keep_default_na=False)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format"
            )

        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]

        # Detect column types
        schema = DatasetService.detect_column_types(df)

        return df, schema

    @staticmethod
    async def create_dataset(
        db: Session,
        org_id: str,
        uploaded_by: str,
        file: UploadFile,
        name: str
    ) -> Dataset:
        """Create dataset record after parsing"""
        df, schema = await DatasetService.parse_file(file)
        row_count = len(df)

        # Convert schema to JSON string
        schema_json = json.dumps(schema)

        # Store file path reference (in real app, this would be MinIO S3 key)
        # For now, we'll store a placeholder
        file_path = f"uploads/{org_id}/{file.filename}" if file.filename else "uploads/unknown"

        dataset = Dataset(
            id="00000000-0000-0000-0000-000000000000",  # Will be DB-generated
            org_id=org_id,
            uploaded_by=uploaded_by,
            name=name,
            source_type=file.filename.split(".")[-1].upper() if file.filename else "CSV",
            file_path=file_path,
            schema_json=schema_json,
            row_count=row_count,
            status="processing",
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        return dataset

    @staticmethod
    def get_quality_summary(schema: List[Dict]) -> str:
        """Generate a data quality summary from schema info"""
        issues = []
        for col in schema:
            nullable_pct = col.get("nullable_pct", 0)
            if nullable_pct > 30:
                issues.append(f"Column '{col['column']}' has {nullable_pct:.1f}% missing values")
        if issues:
            return "Data quality issues: " + "; ".join(issues[:5])
        return "No significant data quality issues detected"