from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.payment import PaymentStatus
import re


class CardInput(BaseModel):
    """Card details for payment"""
    number: str = Field(..., description="Card number (16 digits)")
    exp_month: int = Field(..., ge=1, le=12, description="Expiration month (1-12)")
    exp_year: int = Field(..., ge=2024, description="Expiration year")
    cvc: str = Field(..., description="Card security code (3-4 digits)")

    @field_validator('number')
    @classmethod
    def validate_card_number(cls, v):
        # Remove spaces and dashes
        v = re.sub(r'[\s-]', '', v)
        if not v.isdigit() or len(v) not in [15, 16]:
            raise ValueError('Invalid card number format')
        return v

    @field_validator('cvc')
    @classmethod
    def validate_cvc(cls, v):
        if not v.isdigit() or len(v) not in [3, 4]:
            raise ValueError('CVC must be 3 or 4 digits')
        return v


class PaymentCreate(BaseModel):
    """Create a new payment intent"""
    amount: float = Field(..., gt=0, description="Amount in smallest currency unit (e.g., cents)")
    currency: str = Field(default="USD", description="3-letter currency code")
    card: CardInput
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if len(v) != 3 or not v.isalpha():
            raise ValueError('Currency must be a 3-letter code')
        return v.upper()


class PaymentResponse(BaseModel):
    """Payment response"""
    id: str
    amount: float
    currency: str
    status: PaymentStatus
    card_last4: Optional[str]
    card_brand: Optional[str]
    customer_email: Optional[str]
    customer_name: Optional[str]
    description: Optional[str]
    authorization_code: Optional[str]
    error_message: Optional[str]
    payment_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    authorized_at: Optional[datetime]
    captured_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaymentCapture(BaseModel):
    """Capture an authorized payment"""
    amount: Optional[float] = Field(None, gt=0, description="Amount to capture (defaults to full authorization)")


class RefundCreate(BaseModel):
    """Create a refund"""
    amount: Optional[float] = Field(None, gt=0, description="Amount to refund (defaults to full payment)")
    reason: Optional[str] = Field(None, description="Reason for refund")


class RefundResponse(BaseModel):
    """Refund response"""
    id: str
    payment_id: str
    amount: float
    reason: Optional[str]
    status: str
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaymentEventResponse(BaseModel):
    """Payment event response"""
    id: str
    payment_id: str
    event_type: str
    status: str
    data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True
