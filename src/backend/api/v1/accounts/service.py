
from typing import List, Dict, Optional
from backend.core.exceptions import ValidationError, NotFoundError
from datetime import datetime
import uuid

class TradingAccountService:
    """Service for managing trading accounts"""

    def create_account(self, user_id: str, account_data: Dict) -> Dict:
        """Create a new trading account"""
        try:
            # Validate account data
            self._validate_account_data(account_data)
            
            # Create account record
            account_id = str(uuid.uuid4())
            account = {
                "id": account_id,
                "user_id": user_id,
                "name": account_data["name"],
                "broker": account_data.get("broker"),
                "account_type": account_data.get("account_type"),
                "account_number": account_data.get("account_number"),
                "is_active": "true",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Save to database
            saved_account = self._save_account(account)
            return saved_account
            
        except ValidationError:
            raise
        except Exception as e:
            raise Exception(f"Failed to create account: {str(e)}")

    def get_user_accounts(self, user_id: str) -> List[Dict]:
        """Get all trading accounts for a user"""
        try:
            accounts = self._get_accounts_by_user(user_id)
            return accounts
        except Exception as e:
            raise Exception(f"Failed to retrieve accounts: {str(e)}")

    def get_account_by_id(self, account_id: str, user_id: str) -> Optional[Dict]:
        """Get a specific trading account by ID"""
        try:
            account = self._get_account_from_db(account_id, user_id)
            return account
        except Exception as e:
            raise Exception(f"Failed to retrieve account: {str(e)}")

    def update_account(self, account_id: str, user_id: str, update_data: Dict) -> Optional[Dict]:
        """Update a trading account"""
        try:
            # Validate update data
            self._validate_update_data(update_data)
            
            # Get existing account
            existing_account = self._get_account_from_db(account_id, user_id)
            if not existing_account:
                return None
            
            # Update fields
            update_data["updated_at"] = datetime.now()
            updated_account = self._update_account_in_db(account_id, user_id, update_data)
            return updated_account
            
        except ValidationError:
            raise
        except Exception as e:
            raise Exception(f"Failed to update account: {str(e)}")

    def delete_account(self, account_id: str, user_id: str) -> bool:
        """Delete a trading account"""
        try:
            # Check if account exists
            account = self._get_account_from_db(account_id, user_id)
            if not account:
                return False
            
            # Mark as inactive instead of hard delete to preserve trade history
            self._update_account_in_db(account_id, user_id, {
                "is_active": "false",
                "updated_at": datetime.now()
            })
            return True
            
        except Exception as e:
            raise Exception(f"Failed to delete account: {str(e)}")

    def _validate_account_data(self, account_data: Dict) -> bool:
        """Validate account creation data"""
        if not account_data.get("name") or not account_data["name"].strip():
            raise ValidationError("Account name is required")
        
        if len(account_data["name"]) > 100:
            raise ValidationError("Account name too long")
        
        if account_data.get("account_type") and account_data["account_type"] not in ["sim", "funded", "live", "demo"]:
            raise ValidationError("Invalid account type")
        
        return True

    def _validate_update_data(self, update_data: Dict) -> bool:
        """Validate account update data"""
        if "name" in update_data:
            if not update_data["name"] or not update_data["name"].strip():
                raise ValidationError("Account name cannot be empty")
            if len(update_data["name"]) > 100:
                raise ValidationError("Account name too long")
        
        if "account_type" in update_data and update_data["account_type"]:
            if update_data["account_type"] not in ["sim", "funded", "live", "demo"]:
                raise ValidationError("Invalid account type")
        
        return True

    def _save_account(self, account: Dict) -> Dict:
        """Save account to database"""
        # Mock implementation - replace with actual database save
        return account

    def _get_accounts_by_user(self, user_id: str) -> List[Dict]:
        """Get accounts by user ID from database"""
        # Mock implementation - replace with actual database query
        return []

    def _get_account_from_db(self, account_id: str, user_id: str) -> Optional[Dict]:
        """Get account from database"""
        # Mock implementation - replace with actual database query
        return None

    def _update_account_in_db(self, account_id: str, user_id: str, update_data: Dict) -> Optional[Dict]:
        """Update account in database"""
        # Mock implementation - replace with actual database update
        return None
