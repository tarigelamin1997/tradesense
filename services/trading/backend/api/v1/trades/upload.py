"""
CSV Upload endpoint for trades
"""
import csv
import io
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from core.db.session import get_db
from api.deps import get_current_user
from models.user import User
from models.trade import Trade
from api.v1.trades.service import TradesService

router = APIRouter()

class CSVTradeRow(BaseModel):
    """Model for validating CSV trade data"""
    symbol: str = Field(..., min_length=1, max_length=20)
    side: str = Field(..., pattern="^(long|short)$")
    entry_price: float = Field(..., gt=0)
    exit_price: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)
    entry_date: str
    exit_date: str = None
    strategy: str = Field(None, max_length=100)
    notes: str = Field(None, max_length=1000)
    
    @validator('entry_date', 'exit_date')
    def validate_date(cls, v):
        if v:
            try:
                # Try multiple date formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%m/%d/%Y', '%m/%d/%Y %H:%M:%S']:
                    try:
                        datetime.strptime(v, fmt)
                        return v
                    except ValueError:
                        continue
                raise ValueError(f"Invalid date format: {v}")
            except Exception:
                raise ValueError(f"Invalid date format: {v}")
        return v

class UploadResponse(BaseModel):
    """Response model for CSV upload"""
    message: str
    trades_imported: int
    trades_skipped: int
    errors: List[str] = []

def get_trade_service(db: Session = Depends(get_db)) -> TradesService:
    return TradesService(db)

@router.post("/upload", response_model=UploadResponse)
async def upload_trades_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    trade_service: TradesService = Depends(get_trade_service)
):
    """
    Upload trades from a CSV file
    
    Expected CSV columns:
    - symbol: Trading symbol (e.g., AAPL, TSLA)
    - side: Trade direction (long/short)
    - entry_price: Entry price
    - exit_price: Exit price
    - quantity: Number of shares/contracts
    - entry_date: Entry date (YYYY-MM-DD or MM/DD/YYYY)
    - exit_date: Exit date (optional)
    - strategy: Trading strategy (optional)
    - notes: Trade notes (optional)
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    # Validate file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum allowed size is 10MB"
        )
    
    # Process CSV
    trades_imported = 0
    trades_skipped = 0
    errors = []
    
    try:
        # Decode CSV content
        csv_text = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        
        # Validate headers
        required_headers = {'symbol', 'side', 'entry_price', 'exit_price', 'quantity', 'entry_date'}
        if not required_headers.issubset(set(csv_reader.fieldnames or [])):
            missing = required_headers - set(csv_reader.fieldnames or [])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing)}"
            )
        
        # Process each row
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header
            try:
                # Clean and validate row data
                trade_data = CSVTradeRow(
                    symbol=row.get('symbol', '').strip().upper(),
                    side=row.get('side', '').strip().lower(),
                    entry_price=float(row.get('entry_price', 0)),
                    exit_price=float(row.get('exit_price', 0)),
                    quantity=float(row.get('quantity', 0)),
                    entry_date=row.get('entry_date', '').strip(),
                    exit_date=row.get('exit_date', '').strip() or None,
                    strategy=row.get('strategy', '').strip() or None,
                    notes=row.get('notes', '').strip() or None
                )
                
                # Calculate P&L
                if trade_data.side == 'long':
                    pnl = (trade_data.exit_price - trade_data.entry_price) * trade_data.quantity
                else:  # short
                    pnl = (trade_data.entry_price - trade_data.exit_price) * trade_data.quantity
                
                # Create trade
                trade = Trade(
                    user_id=current_user.id,
                    symbol=trade_data.symbol,
                    side=trade_data.side,
                    entry_price=trade_data.entry_price,
                    exit_price=trade_data.exit_price,
                    quantity=trade_data.quantity,
                    pnl=pnl,
                    entry_date=trade_data.entry_date,
                    exit_date=trade_data.exit_date,
                    strategy=trade_data.strategy,
                    notes=trade_data.notes
                )
                
                db.add(trade)
                trades_imported += 1
                
            except Exception as e:
                trades_skipped += 1
                errors.append(f"Row {row_num}: {str(e)}")
                if len(errors) >= 10:  # Limit error messages
                    errors.append(f"... and {trades_skipped - 10} more errors")
                    break
        
        # Commit all trades
        if trades_imported > 0:
            db.commit()
        
        return UploadResponse(
            message=f"Successfully imported {trades_imported} trades",
            trades_imported=trades_imported,
            trades_skipped=trades_skipped,
            errors=errors[:10]  # Limit to first 10 errors
        )
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file encoding. Please ensure the file is UTF-8 encoded"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV: {str(e)}"
        )