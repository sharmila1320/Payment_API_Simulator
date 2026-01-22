from sqlalchemy import Column, String, Integer, Float, DateTime, Enum as SQLEnum, JSON
from datetime import datetime
import enum
import uuid
from app.database import Base


class PaymentStatus(str, enum.Enum):
    """Payment lifecycle states - standard payment processing"""
    CREATED = "created"  # Payment intent created
    PENDING = "pending"  # Authorization requested
    AUTHORIZED = "authorized"  # Funds reserved but not captured
    PROCESSING = "processing"  # Capture in progress
    SUCCEEDED = "succeeded"  # Payment completed successfully
    FAILED = "failed"  # Payment failed
    CANCELLED = "cancelled"  # Payment cancelled before capture
    REFUND_PENDING = "refund_pending"  # Refund initiated
    REFUNDED = "refunded"  # Fully refunded


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: f"pay_{uuid.uuid4().hex}")
    amount = Column(Float, nullable=False)  # Amount in smallest currency unit (e.g., cents)
    currency = Column(String(3), default="USD")
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.CREATED)

    # Card information (masked for security)
    card_last4 = Column(String(4))
    card_brand = Column(String(20))
    card_exp_month = Column(Integer)
    card_exp_year = Column(Integer)

    # Customer info
    customer_email = Column(String)
    customer_name = Column(String)

    # Payment details
    description = Column(String)
    authorization_code = Column(String)  # Auth code from card network

    # Metadata and audit
    payment_metadata = Column(JSON, default={})
    error_message = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    authorized_at = Column(DateTime, nullable=True)
    captured_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Payment {self.id} {self.status} ${self.amount/100:.2f}>"


class PaymentEvent(Base):
    """Audit log of all payment state transitions"""
    __tablename__ = "payment_events"

    id = Column(String, primary_key=True, default=lambda: f"evt_{uuid.uuid4().hex}")
    payment_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)  # e.g., "payment.authorized", "payment.captured"
    status = Column(String)
    data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PaymentEvent {self.event_type} for {self.payment_id}>"


class Refund(Base):
    """Refund transactions"""
    __tablename__ = "refunds"

    id = Column(String, primary_key=True, default=lambda: f"ref_{uuid.uuid4().hex}")
    payment_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Refund {self.id} ${self.amount/100:.2f} for {self.payment_id}>"
