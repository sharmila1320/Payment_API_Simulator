# Quick Start Guide

Get the Payment API Simulator running in 5 minutes!

## Setup (1 minute)

```bash
# Navigate to project
cd payment-api-simulator

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Start Server (30 seconds)

```bash
uvicorn app.main:app --reload
```

Server runs at: **http://127.0.0.1:8000**

## Test It (2 minutes)

### Option 1: Use Swagger UI (Easiest)

1. Open browser to: **http://127.0.0.1:8000/docs**
2. Click on `POST /payments/` endpoint
3. Click "Try it out"
4. Use this test data:

```json
{
  "amount": 2999,
  "currency": "USD",
  "card": {
    "number": "4242424242424242",
    "exp_month": 12,
    "exp_year": 2025,
    "cvc": "123"
  },
  "customer_email": "test@example.com",
  "customer_name": "Test User",
  "description": "Test payment"
}
```

5. Click "Execute"
6. Copy the `payment_id` from response
7. Try other endpoints: authorize, capture, etc.

### Option 2: Use Example Script

```bash
# In a new terminal (keep server running)
python example_usage.py
```

This runs through the complete payment lifecycle automatically.

### Option 3: Use cURL

```bash
# Create payment
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
    "customer_email": "test@example.com"
  }'

# Copy the payment_id from response, then:

# Authorize
curl -X POST "http://127.0.0.1:8000/payments/{payment_id}/authorize"

# Capture
curl -X POST "http://127.0.0.1:8000/payments/{payment_id}/capture"

# View history
curl "http://127.0.0.1:8000/payments/{payment_id}/events"
```

## Understanding the Flow

1. **Create** - Initialize payment with card details
   - Status: `created`

2. **Authorize** - Reserve funds on card
   - Status: `authorized`
   - Money is held but not transferred yet

3. **Capture** - Actually transfer the money
   - Status: `succeeded`
   - Merchant receives funds

This two-phase commit is how real payment processors work!

## Test Cards

| Card Number         | Result   |
|--------------------|----------|
| 4242424242424242   | Success  |
| 5555555555554444   | Success  |
| 4000000000000002   | Decline  |

All cards accept:
- Any future expiry date
- Any 3-digit CVC

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the Swagger UI: http://127.0.0.1:8000/docs
- Try different test scenarios with `example_usage.py`
- Inspect the database: `sqlite3 payment_simulator.db`

## Common Issues

**Port already in use?**
```bash
uvicorn app.main:app --reload --port 8001
```

**Import errors?**
```bash
# Make sure virtual environment is activated
which python  # Should show venv path
pip install -r requirements.txt
```

**Database issues?**
```bash
rm payment_simulator.db
# Restart server - it will recreate the database
```

## What You're Learning

- **Two-phase commit**: Authorization vs Capture
- **State machines**: Payment lifecycle transitions
- **Card validation**: Luhn algorithm, brand detection
- **RESTful APIs**: Resource-oriented design
- **Audit trails**: Event logging
- **Payment security**: Card masking, PCI concepts

Happy learning!
