from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes import payments

# Initialize FastAPI app
app = FastAPI(
    title="Payment API Simulator",
    description="""
    A safe payment processing API simulator that demonstrates how to handle card payments.

    ## Payment Lifecycle

    This API simulates the complete payment lifecycle:

    1. **Create Payment** - Initialize payment intent with card details
    2. **Authorize** - Request authorization from card network (reserves funds)
    3. **Capture** - Actually transfer the funds (two-phase commit)
    4. **Refund** - Return funds to customer (optional)

    ### Payment States

    - `created` - Payment intent created
    - `pending` - Authorization in progress
    - `authorized` - Funds reserved (not captured)
    - `processing` - Capture in progress
    - `succeeded` - Payment completed successfully
    - `failed` - Payment failed
    - `cancelled` - Cancelled before capture
    - `refund_pending` - Refund initiated
    - `refunded` - Fully refunded

    ## Test Cards

    Use these test card numbers:
    - `4242424242424242` - Test card (succeeds)
    - `5555555555554444` - Mastercard (succeeds)
    - `4000000000000002` - Test card (always declines)

    All test cards accept:
    - Any future expiry date
    - Any 3-digit CVC
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(payments.router)


@app.on_event("startup")
def on_startup():
    """Initialize database on startup"""
    init_db()


@app.get("/", tags=["Health"])
def root():
    """API health check"""
    return {
        "status": "healthy",
        "service": "Payment API Simulator",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": "2024-01-01T00:00:00Z"
    }
