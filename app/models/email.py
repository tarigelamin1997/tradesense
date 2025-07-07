
"""
Email Models
Pydantic models for email scheduling and templates
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import time, datetime

class EmailSchedule(BaseModel):
    id: int
    user_id: int
    email_type: str
    schedule_time: time
    enabled: bool
    recipients: List[EmailStr]
    created_at: datetime

class EmailTemplate(BaseModel):
    id: str
    name: str
    subject: str
    template_html: str
    template_text: str

class EmailReport(BaseModel):
    user_id: int
    report_type: str
    generated_at: datetime
    content: dict
