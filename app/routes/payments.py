from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.schemas import (
    PaymentCreate,
    PaymentResponse,
    PaymentCapture,
    RefundCreate,
    RefundResponse,
    PaymentEventResponse
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new payment intent

    This is Step 1 of the payment flow:
    - Validates card details
    - Creates payment record
    - Returns payment ID for subsequent operations
    """
    service = PaymentService(db)
    try:
        payment = service.create_payment(payment_data)
        return payment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{payment_id}/authorize", response_model=PaymentResponse)
def authorize_payment(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """
    Authorize a payment

    This is Step 2 of the payment flow:
    - Requests authorization from card network
    - Reserves funds on customer's card
    - Does NOT capture funds yet (two-phase commit)

    Status transitions: CREATED -> PENDING -> AUTHORIZED (or FAILED)
    """
    service = PaymentService(db)
    try:
        payment = service.authorize_payment(payment_id)
        return payment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{payment_id}/capture", response_model=PaymentResponse)
def capture_payment(
    payment_id: str,
    capture_data: PaymentCapture = None,
    db: Session = Depends(get_db)
):
    """
    Capture an authorized payment

    This is Step 3 of the payment flow:
    - Actually transfers funds from customer to merchant
    - Can capture full or partial amount
    - This is when money actually moves

    Status transitions: AUTHORIZED -> PROCESSING -> SUCCEEDED (or FAILED)
    """
    service = PaymentService(db)
    try:
        amount = capture_data.amount if capture_data else None
        payment = service.capture_payment(payment_id, amount)
        return payment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
def cancel_payment(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancel an authorized payment

    - Releases the hold on funds
    - Can only cancel before capture
    - After capture, use refund instead

    Status transitions: CREATED/AUTHORIZED -> CANCELLED
    """
    service = PaymentService(db)
    try:
        payment = service.cancel_payment(payment_id)
        return payment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{payment_id}/refunds", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
def create_refund(
    payment_id: str,
    refund_data: RefundCreate,
    db: Session = Depends(get_db)
):
    """
    Refund a succeeded payment

    - Returns funds to customer
    - Can be full or partial refund
    - Only works on succeeded payments

    Status transitions: SUCCEEDED -> REFUND_PENDING -> REFUNDED
    """
    service = PaymentService(db)
    try:
        refund = service.create_refund(payment_id, refund_data)
        return refund
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve payment details

    Returns current state and all payment information
    """
    service = PaymentService(db)
    try:
        payment = service.get_payment(payment_id)
        return payment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{payment_id}/events", response_model=List[PaymentEventResponse])
def get_payment_events(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """
    Get payment event history

    Returns audit trail of all state transitions and events
    for this payment. Useful for debugging and compliance.
    """
    service = PaymentService(db)
    try:
        events = service.get_payment_events(payment_id)
        return events
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
