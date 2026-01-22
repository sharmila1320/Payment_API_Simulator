# Payment Flow Explained

## Complete Payment Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PAYMENT LIFECYCLE                            │
└─────────────────────────────────────────────────────────────────────┘

1. CREATE PAYMENT
   ┌──────────────────┐
   │   POST /payments │  ➜  Card validation
   └──────────────────┘     Luhn check, expiry check
          ↓
      [CREATED]  ➜  Payment intent stored in database
          ↓

2. AUTHORIZE
   ┌─────────────────────────┐
   │ POST /payments/{id}/    │  ➜  Contact card network
   │        authorize        │     Check funds availability
   └─────────────────────────┘     Reserve funds (hold)
          ↓
      [PENDING]  ➜  Authorization in progress
          ↓
      [AUTHORIZED]  ➜  Funds reserved, auth code received
          │            Money NOT transferred yet!
          │            Customer sees "pending" on their statement
          │
          ├──────────────┐
          │              │
          ↓              ↓
    [CONTINUE]      [CANCELLED]  ➜  Release hold
          │                         Customer never charged
          ↓

3. CAPTURE
   ┌─────────────────────────┐
   │ POST /payments/{id}/    │  ➜  Actually move money
   │        capture          │     From customer to merchant
   └─────────────────────────┘
          ↓
      [PROCESSING]  ➜  Capture in progress
          ↓
      [SUCCEEDED]  ➜  Payment complete!
          │           Merchant receives funds
          │           Customer charged
          │
          ↓

4. REFUND (Optional)
   ┌─────────────────────────┐
   │ POST /payments/{id}/    │  ➜  Return money to customer
   │        refunds          │
   └─────────────────────────┘
          ↓
   [REFUND_PENDING]  ➜  Refund in progress
          ↓
      [REFUNDED]  ➜  Money returned to customer
```

## State Transitions

```
CREATED ──────┐
              ↓
          PENDING ─────→ FAILED (auth declined)
              ↓
         AUTHORIZED ────→ CANCELLED (before capture)
              ↓
         PROCESSING ────→ FAILED (capture failed)
              ↓
          SUCCEEDED ─────→ REFUND_PENDING ──→ REFUNDED
```

## Two-Phase Commit: Why?

### Authorization (Phase 1)
```
Customer: "I want to buy this"
Merchant: "Let me check if you have money"
Bank: "Yes, they have $50. I'll hold it for you"
        [Funds reserved but not transferred]
```

**Why authorize first?**
- Verify customer has funds before shipping product
- Reserve funds so they don't spend it elsewhere
- Allow time to prepare order before charging
- Can cancel if order is cancelled

### Capture (Phase 2)
```
Merchant: "Product shipped, please transfer the money"
Bank: "Okay, moving $50 from customer to merchant"
      [Money actually transferred]
```

**Why separate capture?**
- Only charge when product ships
- Can capture less than authorized (e.g., partial shipment)
- Can cancel if unable to fulfill order

## Real-World Example: Online Store

### Scenario: Customer buys $100 headphones

```
Day 1 - Order Placed
├─ Create Payment ($100)
├─ Authorize ($100)
│  └─ Customer sees "$100 pending" on card
│  └─ Merchant hasn't received money yet
│  └─ Money is "held" by bank
└─ Merchant prepares shipment

Day 2 - Product Ships
├─ Capture ($100)
│  └─ Money transfers from customer to merchant
│  └─ Customer sees "$100 charged" on statement
└─ Product in transit

Day 5 - Customer Receives
└─ If damaged/wrong item:
   └─ Refund ($100)
      └─ Money returned to customer
```

### What if order is cancelled on Day 1?

```
Day 1 - Order Cancelled Before Shipping
├─ Cancel Payment
│  └─ Release hold on $100
│  └─ Customer NEVER charged
│  └─ "Pending" charge disappears
└─ Merchant never receives money
```

## Authorization vs Capture: Key Differences

| Aspect | Authorization | Capture |
|--------|--------------|---------|
| **Money moved?** | No, just reserved | Yes, actually transferred |
| **Customer sees** | "Pending" charge | Actual charge |
| **Merchant gets?** | Nothing yet | Receives funds |
| **Can cancel?** | Yes, easily | No, must refund |
| **Bank action** | Hold funds | Transfer funds |
| **Expires** | Usually 7 days | Permanent (until refunded) |

## Common Patterns

### Pattern 1: Immediate Capture (Most Common)
```
Create → Authorize → Capture (immediately)
└─ Used for: Digital goods, instant services
└─ Example: Movie rental, music download
```

### Pattern 2: Delayed Capture (E-commerce)
```
Create → Authorize → ... wait ... → Capture (when shipped)
└─ Used for: Physical products
└─ Example: Amazon, most online stores
```

### Pattern 3: Authorization Only
```
Create → Authorize → ... wait ... → Cancel
└─ Used for: Pre-orders, temporary holds
└─ Example: Hotel booking, car rental
```

### Pattern 4: Partial Capture
```
Create → Authorize ($100) → Capture ($80)
└─ Used for: Partial shipments, final price adjustments
└─ Example: Pre-order with estimate, final price lower
```

## Error Scenarios

### Declined at Authorization
```
Create [CREATED]
  ↓
Authorize [PENDING]
  ↓
[FAILED] ← Insufficient funds / Card declined
└─ Customer never charged
└─ Merchant notified immediately
```

### Failed at Capture
```
Create [CREATED]
  ↓
Authorize [AUTHORIZED] ← Funds reserved successfully
  ↓
Capture [PROCESSING]
  ↓
[FAILED] ← Insufficient funds / Card cancelled / Expired hold
└─ Rare but possible
└─ Hold released, customer not charged
```

## API Endpoints Summary

| Endpoint | Method | Purpose | Status Change |
|----------|--------|---------|---------------|
| `/payments/` | POST | Create payment | → CREATED |
| `/payments/{id}/authorize` | POST | Reserve funds | CREATED → AUTHORIZED |
| `/payments/{id}/capture` | POST | Transfer money | AUTHORIZED → SUCCEEDED |
| `/payments/{id}/cancel` | POST | Release hold | AUTHORIZED → CANCELLED |
| `/payments/{id}/refunds` | POST | Return money | SUCCEEDED → REFUNDED |
| `/payments/{id}` | GET | Check status | - |
| `/payments/{id}/events` | GET | View history | - |

## Database Tables

### payments
```
id, amount, currency, status, card_last4, card_brand,
authorization_code, created_at, authorized_at, captured_at
```

### payment_events
```
id, payment_id, event_type, status, data, created_at
```

### refunds
```
id, payment_id, amount, reason, status, created_at
```

## Security Best Practices

### What This Simulator Does
- ✅ Validates card with Luhn algorithm
- ✅ Checks expiry dates
- ✅ Masks card numbers (only show last 4)
- ✅ Never logs full card numbers
- ✅ Tracks all events for audit

### What Real Systems Need (Beyond This Simulator)
- 🔒 PCI DSS compliance
- 🔒 Tokenization (never store real cards)
- 🔒 HTTPS/TLS encryption
- 🔒 3D Secure authentication
- 🔒 Fraud detection
- 🔒 Rate limiting
- 🔒 API key authentication

## Learning Resources

### Concepts Demonstrated
- **Two-Phase Commit**: Database transaction pattern
- **State Machine**: Finite state transitions
- **RESTful API**: Resource-oriented design
- **Idempotency**: Safe to retry operations
- **Audit Logging**: Complete event trail
- **Validation**: Input validation and business rules

### Real-World Equivalents
- **This API** → Industry-standard payment processing APIs
- **Authorization** → ISO 8583 0100 message
- **Capture** → ISO 8583 0200 message
- **Refund** → ISO 8583 0400 message

## Testing Tips

### Test Successful Flow
1. Use card `4242424242424242`
2. Any future expiry, any CVC
3. Follow: Create → Authorize → Capture

### Test Declined Card
1. Use card `4000000000000002`
2. Should fail at authorization step

### Test Cancellation
1. Create and authorize payment
2. Cancel before capture
3. Verify status is CANCELLED

### Test Refund
1. Complete full payment flow
2. Create refund
3. Check payment status is REFUNDED

Happy learning!
