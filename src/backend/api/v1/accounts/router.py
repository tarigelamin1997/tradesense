from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from models.trading_account import TradingAccountCreate, TradingAccountUpdate, TradingAccountResponse
from api.v1.accounts.service import TradingAccountService
from api.deps import get_current_user
from models.user import UserRead

router = APIRouter(tags=["Trading Accounts"])

@router.post("/", response_model=TradingAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_trading_account(
    account_data: TradingAccountCreate,
    current_user: UserRead = Depends(get_current_user)
):
    """Create a new trading account for the current user"""
    service = TradingAccountService()
    try:
        account = service.create_account(current_user.id, account_data.dict())
        return account
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create trading account: {str(e)}"
        )

@router.get("/", response_model=List[TradingAccountResponse])
async def get_user_accounts(
    current_user: UserRead = Depends(get_current_user)
):
    """Get all trading accounts for the current user"""
    service = TradingAccountService()
    try:
        accounts = service.get_user_accounts(current_user.id)
        return accounts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve accounts: {str(e)}"
        )

@router.get("/{account_id}", response_model=TradingAccountResponse)
async def get_account(
    account_id: str,
    current_user: UserRead = Depends(get_current_user)
):
    """Get a specific trading account"""
    service = TradingAccountService()
    try:
        account = service.get_account_by_id(account_id, current_user.id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
        return account
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve account: {str(e)}"
        )

@router.put("/{account_id}", response_model=TradingAccountResponse)
async def update_account(
    account_id: str,
    update_data: TradingAccountUpdate,
    current_user: UserRead = Depends(get_current_user)
):
    """Update a trading account"""
    service = TradingAccountService()
    try:
        account = service.update_account(account_id, current_user.id, update_data.dict(exclude_unset=True))
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
        return account
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update account: {str(e)}"
        )

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    current_user: UserRead = Depends(get_current_user)
):
    """Delete a trading account"""
    service = TradingAccountService()
    try:
        success = service.delete_account(account_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trading account not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )
