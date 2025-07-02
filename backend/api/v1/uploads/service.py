
"""
Uploads service layer - handles file uploads and data processing
"""
from typing import Dict, List, Any, Optional
import pandas as pd
import uuid
import os
import logging
from datetime import datetime

from backend.api.v1.uploads.schemas import (
    FileUploadResponse,
    DataValidationResult,
    ColumnMappingRequest,
    BulkImportResponse
)
from backend.core.exceptions import ValidationError, BusinessLogicError
from backend.core.config import settings

logger = logging.getLogger(__name__)


class UploadsService:
    """Service for handling file uploads and data processing"""
    
    def __init__(self):
        # In production, this would be a proper cache/database
        self._upload_storage = {}
        self._temp_dir = "temp_uploads"
        os.makedirs(self._temp_dir, exist_ok=True)
    
    async def process_file_upload(self, user_id: str, file) -> FileUploadResponse:
        """Process uploaded file and return metadata"""
        try:
            # Validate file
            if not file.filename:
                raise ValidationError("No file provided")
            
            file_ext = '.' + file.filename.split('.')[-1].lower()
            if file_ext not in settings.allowed_file_extensions:
                raise ValidationError(
                    f"Unsupported file format. Allowed: {', '.join(settings.allowed_file_extensions)}"
                )
            
            # Check file size
            content = await file.read()
            if len(content) > settings.max_file_size:
                raise ValidationError("File too large. Maximum size: 10MB")
            
            # Generate upload ID and save temporarily
            upload_id = str(uuid.uuid4())
            temp_path = os.path.join(self._temp_dir, f"{upload_id}_{file.filename}")
            
            with open(temp_path, "wb") as f:
                f.write(content)
            
            # Read and process file
            try:
                if file_ext == '.csv':
                    df = pd.read_csv(temp_path)
                else:
                    df = pd.read_excel(temp_path)
            except Exception as e:
                raise ValidationError(f"Failed to read file: {str(e)}")
            
            if df.empty:
                raise ValidationError("File is empty")
            
            # Store upload metadata
            upload_data = {
                "upload_id": upload_id,
                "user_id": user_id,
                "filename": file.filename,
                "file_path": temp_path,
                "dataframe": df,
                "uploaded_at": datetime.utcnow(),
                "processed": False
            }
            
            self._upload_storage[upload_id] = upload_data
            
            # Create preview (first 5 rows)
            preview_data = df.head(5).to_dict('records')
            
            logger.info(f"File {file.filename} uploaded successfully for user {user_id}")
            
            return FileUploadResponse(
                success=True,
                filename=file.filename,
                rows=len(df),
                columns=list(df.columns),
                data_preview=preview_data,
                message="File uploaded and processed successfully",
                upload_id=upload_id
            )
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"File upload failed for user {user_id}: {str(e)}")
            raise BusinessLogicError(f"File upload failed: {str(e)}")
    
    async def validate_data(self, upload_id: str, column_mapping: Optional[Dict[str, str]] = None) -> DataValidationResult:
        """Validate uploaded data"""
        try:
            upload_data = self._upload_storage.get(upload_id)
            if not upload_data:
                raise ValidationError("Upload not found")
            
            df = upload_data["dataframe"]
            errors = []
            warnings = []
            
            # Apply column mapping if provided
            if column_mapping:
                try:
                    df = df.rename(columns=column_mapping)
                except Exception as e:
                    errors.append(f"Column mapping failed: {str(e)}")
            
            # Validate required columns
            required_columns = ['symbol', 'pnl']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                errors.append(f"Missing required columns: {missing_columns}")
            
            # Validate data types and values
            if 'pnl' in df.columns:
                try:
                    df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')
                    null_pnl = df['pnl'].isnull().sum()
                    if null_pnl > 0:
                        warnings.append(f"{null_pnl} rows have invalid P&L values")
                except Exception as e:
                    errors.append(f"P&L column validation failed: {str(e)}")
            
            # Validate symbols
            if 'symbol' in df.columns:
                empty_symbols = df['symbol'].isnull().sum()
                if empty_symbols > 0:
                    warnings.append(f"{empty_symbols} rows have missing symbols")
            
            # Validate dates if present
            date_columns = ['entry_time', 'exit_time']
            for col in date_columns:
                if col in df.columns:
                    try:
                        pd.to_datetime(df[col], errors='coerce')
                        invalid_dates = df[col].isnull().sum()
                        if invalid_dates > 0:
                            warnings.append(f"{invalid_dates} rows have invalid {col}")
                    except Exception as e:
                        warnings.append(f"Date validation failed for {col}: {str(e)}")
            
            # Count valid rows
            valid_rows = len(df)
            if 'pnl' in df.columns:
                valid_rows = len(df[df['pnl'].notnull()])
            
            is_valid = len(errors) == 0
            
            result = DataValidationResult(
                valid=is_valid,
                errors=errors,
                warnings=warnings,
                processed_rows=valid_rows,
                total_rows=len(df)
            )
            
            logger.info(f"Data validation completed for upload {upload_id}: {valid_rows}/{len(df)} valid rows")
            
            return result
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Data validation failed for upload {upload_id}: {str(e)}")
            raise BusinessLogicError(f"Data validation failed: {str(e)}")
    
    async def import_trades(self, user_id: str, upload_id: str, column_mapping: Optional[Dict[str, str]] = None) -> BulkImportResponse:
        """Import trades from uploaded data"""
        try:
            upload_data = self._upload_storage.get(upload_id)
            if not upload_data:
                raise ValidationError("Upload not found")
            
            if upload_data["user_id"] != user_id:
                raise ValidationError("Access denied to this upload")
            
            df = upload_data["dataframe"]
            
            # Apply column mapping
            if column_mapping:
                df = df.rename(columns=column_mapping)
            
            # Validate data first
            validation_result = await self.validate_data(upload_id, column_mapping)
            
            if not validation_result.valid:
                return BulkImportResponse(
                    success=False,
                    imported_trades=0,
                    failed_trades=len(df),
                    validation_result=validation_result,
                    message="Validation failed, no trades imported"
                )
            
            # Process trades (in production, this would save to database)
            imported_count = 0
            failed_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Create trade record (simplified for demo)
                    trade_data = {
                        "user_id": user_id,
                        "symbol": row.get("symbol"),
                        "pnl": row.get("pnl"),
                        "entry_time": row.get("entry_time"),
                        "exit_time": row.get("exit_time"),
                        "entry_price": row.get("entry_price"),
                        "exit_price": row.get("exit_price"),
                        "created_at": datetime.utcnow()
                    }
                    
                    # Skip invalid records
                    if pd.isna(trade_data["symbol"]) or pd.isna(trade_data["pnl"]):
                        failed_count += 1
                        continue
                    
                    # In production: save to database
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import row {index}: {str(e)}")
                    failed_count += 1
            
            # Mark upload as processed
            upload_data["processed"] = True
            
            logger.info(f"Bulk import completed for user {user_id}: {imported_count} imported, {failed_count} failed")
            
            return BulkImportResponse(
                success=imported_count > 0,
                imported_trades=imported_count,
                failed_trades=failed_count,
                validation_result=validation_result,
                message=f"Import completed: {imported_count} trades imported, {failed_count} failed"
            )
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Bulk import failed for user {user_id}: {str(e)}")
            raise BusinessLogicError(f"Bulk import failed: {str(e)}")
    
    async def get_upload_status(self, user_id: str, upload_id: str) -> Dict[str, Any]:
        """Get upload status and metadata"""
        try:
            upload_data = self._upload_storage.get(upload_id)
            if not upload_data:
                raise ValidationError("Upload not found")
            
            if upload_data["user_id"] != user_id:
                raise ValidationError("Access denied to this upload")
            
            return {
                "upload_id": upload_id,
                "filename": upload_data["filename"],
                "uploaded_at": upload_data["uploaded_at"],
                "processed": upload_data["processed"],
                "rows": len(upload_data["dataframe"]),
                "columns": list(upload_data["dataframe"].columns)
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get upload status: {str(e)}")
            raise BusinessLogicError(f"Failed to get upload status: {str(e)}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files (should be called periodically)"""
        try:
            for upload_id, upload_data in list(self._upload_storage.items()):
                # Remove files older than 24 hours
                if (datetime.utcnow() - upload_data["uploaded_at"]).total_seconds() > 86400:
                    try:
                        os.remove(upload_data["file_path"])
                        del self._upload_storage[upload_id]
                        logger.info(f"Cleaned up old upload {upload_id}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup upload {upload_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Cleanup task failed: {str(e)}")
