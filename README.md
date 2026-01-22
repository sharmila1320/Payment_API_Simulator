# Payment API Simulator

A safe, educational API that simulates card payment processing. Learn every step of the payment lifecycle with a fully functional REST API backed by SQLite and documented with Swagger UI.

## Features

- **Complete Payment Lifecycle**: Create, Authorize, Capture, Cancel, and Refund
- **State Machine**: Follows real-world payment processing states
- **Card Validation**: Luhn algorithm check, expiry validation, brand detection
- **Audit Trail**: Complete event history for every payment
- **SQLite Persistence**: All payments stored in database
- **Interactive Swagger UI**: Test all endpoints in your browser
- **Test Cards**: Safe card numbers for testing different scenarios

## Payment Flow

### Two-Phase Commit (Auth + Capture)

Modern payment processors use a two-phase commit:

1. **Authorization**: Reserve funds on customer's card (doesn't transfer money yet)
2. **Capture**: Actually transfer the funds

This allows merchants to:
- Verify funds availability before shipping products
- Capture different amounts than authorized (e.g., add shipping costs)
- Cancel if order is cancelled before shipping

### Payment States

```
CREATED → PENDING → AUTHORIZED → PROCESSING → SUCCEEDED
                        ↓              ↓
                   CANCELLED      FAILED

SUCCEEDED → REFUND_PENDING → REFUNDED
```

## Installation

### Prerequisites

- Python 3.9+
- pip

### Setup

```bash
# Clone or navigate to project directory
cd payment-api-simulator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

## Running the API

```bash
# Start the server
uvicorn app.main:app --reload

# Server will start at: http://127.0.0.1:8000
# Swagger UI docs: http://127.0.0.1:8000/docs
# ReDoc docs: http://127.0.0.1:8000/redoc
```

## API Usage

### 1. Create a Payment

```bash
curl -X POST "http://127.0.0.1:8000/payments/" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2999,
    "currency": "USD",
    "card": {
      "number": "4242424242424242",
      "exp_month": 12,
      "exp_year": 2025,
      "cvc": "123"
    },
    "customer_email": "customer@example.com",
    "customer_name": "John Doe",
    "description": "Test payment"
  }'
```

Response:
```json
{
  "id": "pay_abc123",
  "amount": 2999,
  "currency": "USD",
  "status": "created",
  "card_last4": "4242",
  "card_brand": "card",
  "customer_email": "customer@example.com",
  "created_at": "2024-01-01T00:00:00"
}
```

### 2. Authorize the Payment

```bash
curl -X POST "http://127.0.0.1:8000/payments/pay_abc123/authorize"
```

Response:
```json
{
  "id": "pay_abc123",
  "status": "authorized",
  "authorization_code": "A1B2C3",
  "authorized_at": "2024-01-01T00:00:05"
}
```

### 3. Capture the Payment

```bash
curl -X POST "http://127.0.0.1:8000/payments/pay_abc123/capture"
```

Response:
```json
{
  "id": "pay_abc123",
  "status": "succeeded",
  "captured_at": "2024-01-01T00:00:10"
}
```

### 4. View Payment History

```bash
curl "http://127.0.0.1:8000/payments/pay_abc123/events"
```

Response:
```json
[
  {
    "id": "evt_1",
    "event_type": "payment.created",
    "status": "created",
    "created_at": "2024-01-01T00:00:00"
  },
  {
    "id": "evt_2",
    "event_type": "payment.authorized",
    "status": "authorized",
    "created_at": "2024-01-01T00:00:05"
  },
  {
    "id": "evt_3",
    "event_type": "payment.succeeded",
    "status": "succeeded",
    "created_at": "2024-01-01T00:00:10"
  }
]
```

### 5. Refund a Payment

```bash
curl -X POST "http://127.0.0.1:8000/payments/pay_abc123/refunds" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2999,
    "reason": "Customer requested refund"
  }'
```

## Test Cards

Use these card numbers for testing:

| Card Number          | Brand      | Result   | Use Case                    |
|---------------------|------------|----------|----------------------------|
| 4242424242424242    | Card       | Success  | Standard successful payment |
| 5555555555554444    | Mastercard | Success  | Standard successful payment |
| 378282246310005     | Amex       | Success  | 15-digit card              |
| 4000000000000002    | Card       | Decline  | Test declined authorization |

All test cards:
- Accept any future expiry date (e.g., 12/2025)
- Accept any 3-digit CVC (e.g., 123)
- Use amounts in cents (e.g., 2999 = $29.99)

## Project Structure

```
payment-api-simulator/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # SQLAlchemy setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── payment.py       # Database models
│   │   └── schemas.py       # Pydantic schemas
│   ├── routes/
│   │   ├── __init__.py
│   │   └── payments.py      # API endpoints
│   └── services/
│       ├── __init__.py
│       ├── card_validator.py    # Card validation logic
│       └── payment_service.py   # Payment state machine
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Learning Resources

### Key Concepts Demonstrated

1. **Two-Phase Commit**: Separate authorization and capture steps
2. **State Machine**: Well-defined state transitions
3. **Idempotency**: Safe to retry operations
4. **Audit Trail**: Complete event history
5. **Card Security**: Never store full card numbers, use Luhn validation
6. **RESTful Design**: Resource-oriented endpoints

### Real-World Equivalents

This API follows industry-standard payment processing:
- Payment Intent → Confirmation → Capture
- Authorization → Settlement
- Order → Authorize → Capture

## Database

The API uses SQLite for persistence. The database file `payment_simulator.db` will be created automatically on first run.

### Tables

- **payments**: All payment records
- **payment_events**: Audit log of state transitions
- **refunds**: Refund transactions

To inspect the database:

```bash
sqlite3 payment_simulator.db
```

```sql
-- View all payments
SELECT id, amount, status, created_at FROM payments;

-- View payment events
SELECT payment_id, event_type, status, created_at FROM payment_events;
```

## Security Notes

This is a **simulator for learning purposes**. In production:

1. Never store full card numbers (use tokenization)
2. Use PCI DSS compliant payment processors
3. Encrypt sensitive data at rest and in transit
4. Implement proper authentication and authorization
5. Use HTTPS for all API calls
6. Implement rate limiting
7. Log all security-relevant events

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://127.0.0.1:8000/docs
  - Interactive API documentation
  - Test endpoints directly in browser
  - See request/response schemas

- **ReDoc**: http://127.0.0.1:8000/redoc
  - Alternative documentation format
  - Better for reading and reference

## Troubleshooting

### Port Already in Use

```bash
# Use a different port
uvicorn app.main:app --reload --port 8001
```

### Database Locked

```bash
# Delete the database and restart
rm payment_simulator.db
uvicorn app.main:app --reload
```

### Import Errors

```bash
# Make sure you're in the virtual environment
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt
```

## Contributing

This is an educational project. Feel free to:
- Add more test scenarios
- Implement webhook notifications
- Add more payment methods
- Improve error handling
- Add more comprehensive tests

## License

MIT License - Free to use for learning and education.
