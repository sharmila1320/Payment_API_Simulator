from sqlalchemy.orm import Session
from app.models.payment import Payment, PaymentStatus, PaymentEvent, Refund
from app.models.schemas import PaymentCreate, RefundCreate
from app.services.card_validator import validate_card, get_card_brand
from datetime import datetime
import random
import string


class PaymentService:
    """
    Service handling payment lifecycle state machine
    Simulates standard payment processing flow:
    1. CREATED -> Payment intent created
    2. PENDING -> Authorization requested from card network
    3. AUTHORIZED -> Funds reserved (not yet captured)
    4. PROCESSING -> Capture initiated
    5. SUCCEEDED -> Payment completed
    Or FAILED/CANCELLED at any point
    """

    def __init__(self, db: Session):
        self.db = db

    def _log_event(self, payment_id: str, event_type: str, status: str, data: dict = None):
        """Log payment event for audit trail"""
        event = PaymentEvent(
            payment_id=payment_id,
            event_type=event_type,
            status=status,
            data=data or {}
        )
        self.db.add(event)
        self.db.commit()

    def _generate_auth_code(self) -> str:
        """Generate mock authorization code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def create_payment(self, payment_data: PaymentCreate) -> Payment:
        """
        Step 1: Create payment intent
        Validates card and creates payment record
        """
        # Validate card
        is_valid, error = validate_card(
            payment_data.card.number,
            payment_data.card.exp_month,
            payment_data.card.exp_year,
            payment_data.card.cvc
        )

        # Create payment
        payment = Payment(
            amount=payment_data.amount,
            currency=payment_data.currency,
            card_last4=payment_data.card.number[-4:],
            card_brand=get_card_brand(payment_data.card.number),
            card_exp_month=payment_data.card.exp_month,
            card_exp_year=payment_data.card.exp_year,
            customer_email=payment_data.customer_email,
            customer_name=payment_data.customer_name,
            description=payment_data.description,
            payment_metadata=payment_data.metadata,
            status=PaymentStatus.CREATED
        )

        if not is_valid:
            payment.status = PaymentStatus.FAILED
            payment.error_message = error

        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)

        # Log event
        self._log_event(
            payment.id,
            "payment.created",
            payment.status.value,
            {"amount": payment.amount, "currency": payment.currency}
        )

        return payment

    def authorize_payment(self, payment_id: str) -> Payment:
        """
        Step 2: Authorize payment
        Requests authorization from card network to reserve funds
        This is a two-phase commit: authorize first, capture later
        """
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ValueError("Payment not found")

        # Check if payment can be authorized
        if payment.status != PaymentStatus.CREATED:
            raise ValueError(f"Payment cannot be authorized from status: {payment.status}")

        # Update to pending
        payment.status = PaymentStatus.PENDING
        payment.updated_at = datetime.utcnow()
        self.db.commit()

        self._log_event(payment.id, "payment.authorization_requested", PaymentStatus.PENDING.value)

        # Simulate authorization (90% success rate for valid cards)
        if payment.error_message:
            # Card validation failed
            payment.status = PaymentStatus.FAILED
        elif random.random() < 0.9:
            # Authorization successful
            payment.status = PaymentStatus.AUTHORIZED
            payment.authorization_code = self._generate_auth_code()
            payment.authorized_at = datetime.utcnow()
            self._log_event(
                payment.id,
                "payment.authorized",
                PaymentStatus.AUTHORIZED.value,
                {"auth_code": payment.authorization_code}
            )
        else:
            # Authorization declined
            payment.status = PaymentStatus.FAILED
            payment.error_message = "Authorization declined by card issuer"
            self._log_event(payment.id, "payment.failed", PaymentStatus.FAILED.value)

        payment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(payment)

        return payment

    def capture_payment(self, payment_id: str, amount: float = None) -> Payment:
        """
        Step 3: Capture authorized payment
        Actually transfers the funds. Can be partial or full amount.
        This is when the merchant gets paid.
        """
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ValueError("Payment not found")

        if payment.status != PaymentStatus.AUTHORIZED:
            raise ValueError(f"Payment cannot be captured from status: {payment.status}")

        # Use authorized amount if not specified
        capture_amount = amount if amount is not None else payment.amount

        if capture_amount > payment.amount:
            raise ValueError("Capture amount exceeds authorized amount")

        # Update to processing
        payment.status = PaymentStatus.PROCESSING
        payment.updated_at = datetime.utcnow()
        self.db.commit()

        self._log_event(
            payment.id,
            "payment.capture_requested",
            PaymentStatus.PROCESSING.value,
            {"amount": capture_amount}
        )

        # Simulate capture (95% success rate)
        if random.random() < 0.95:
            payment.status = PaymentStatus.SUCCEEDED
            payment.captured_at = datetime.utcnow()
            self._log_event(
                payment.id,
                "payment.succeeded",
                PaymentStatus.SUCCEEDED.value,
                {"amount": capture_amount}
            )
        else:
            payment.status = PaymentStatus.FAILED
            payment.error_message = "Capture failed - insufficient funds"
            self._log_event(payment.id, "payment.failed", PaymentStatus.FAILED.value)

        payment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(payment)

        return payment

    def cancel_payment(self, payment_id: str) -> Payment:
        """
        Cancel an authorized payment before capture
        Releases the hold on funds
        """
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ValueError("Payment not found")

        if payment.status not in [PaymentStatus.CREATED, PaymentStatus.AUTHORIZED]:
            raise ValueError(f"Payment cannot be cancelled from status: {payment.status}")

        payment.status = PaymentStatus.CANCELLED
        payment.updated_at = datetime.utcnow()
        self.db.commit()

        self._log_event(payment.id, "payment.cancelled", PaymentStatus.CANCELLED.value)
        self.db.refresh(payment)

        return payment

    def create_refund(self, payment_id: str, refund_data: RefundCreate) -> Refund:
        """
        Refund a succeeded payment
        Can be partial or full refund
        """
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ValueError("Payment not found")

        if payment.status != PaymentStatus.SUCCEEDED:
            raise ValueError(f"Payment cannot be refunded from status: {payment.status}")

        refund_amount = refund_data.amount if refund_data.amount is not None else payment.amount

        if refund_amount > payment.amount:
            raise ValueError("Refund amount exceeds payment amount")

        # Create refund
        refund = Refund(
            payment_id=payment_id,
            amount=refund_amount,
            reason=refund_data.reason,
            status="pending"
        )
        self.db.add(refund)
        self.db.commit()

        # Update payment status
        payment.status = PaymentStatus.REFUND_PENDING
        payment.updated_at = datetime.utcnow()
        self.db.commit()

        self._log_event(
            payment.id,
            "refund.created",
            PaymentStatus.REFUND_PENDING.value,
            {"refund_id": refund.id, "amount": refund_amount}
        )

        # Simulate refund processing (always succeeds)
        refund.status = "succeeded"
        refund.processed_at = datetime.utcnow()
        payment.status = PaymentStatus.REFUNDED
        payment.updated_at = datetime.utcnow()
        self.db.commit()

        self._log_event(
            payment.id,
            "payment.refunded",
            PaymentStatus.REFUNDED.value,
            {"refund_id": refund.id, "amount": refund_amount}
        )

        self.db.refresh(refund)
        return refund

    def get_payment(self, payment_id: str) -> Payment:
        """Retrieve payment by ID"""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ValueError("Payment not found")
        return payment

    def get_payment_events(self, payment_id: str) -> list[PaymentEvent]:
        """Get all events for a payment"""
        return self.db.query(PaymentEvent).filter(
            PaymentEvent.payment_id == payment_id
        ).order_by(PaymentEvent.created_at).all()
