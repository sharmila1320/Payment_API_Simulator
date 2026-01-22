"""
Example usage of the Payment API Simulator

This script demonstrates the complete payment lifecycle:
1. Create payment
2. Authorize payment
3. Capture payment
4. View payment history
5. Refund payment
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://127.0.0.1:8000"


def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))


def main():
    print("Payment API Simulator - Example Usage")
    print("="*60)

    # Step 1: Create a payment
    print("\n[Step 1] Creating payment...")
    payment_data = {
        "amount": 4999,  # $49.99 in cents
        "currency": "USD",
        "card": {
            "number": "4242424242424242",  # Test card
            "exp_month": 12,
            "exp_year": 2025,
            "cvc": "123"
        },
        "customer_email": "customer@example.com",
        "customer_name": "Jane Smith",
        "description": "Premium subscription - Annual plan",
        "metadata": {
            "order_id": "ORD-12345",
            "subscription_plan": "premium"
        }
    }

    response = requests.post(f"{BASE_URL}/payments/", json=payment_data)
    print_response("Payment Created", response)

    if response.status_code != 201:
        print("\nFailed to create payment. Exiting.")
        return

    payment = response.json()
    payment_id = payment["id"]
    print(f"\nPayment ID: {payment_id}")
    print(f"Status: {payment['status']}")

    time.sleep(1)

    # Step 2: Authorize the payment
    print("\n[Step 2] Authorizing payment...")
    response = requests.post(f"{BASE_URL}/payments/{payment_id}/authorize")
    print_response("Payment Authorized", response)

    payment = response.json()
    print(f"\nStatus: {payment['status']}")
    if payment['status'] == 'authorized':
        print(f"Authorization Code: {payment['authorization_code']}")
        print("Funds are now reserved on customer's card!")
    elif payment['status'] == 'failed':
        print(f"Authorization failed: {payment['error_message']}")
        return

    time.sleep(1)

    # Step 3: Capture the payment
    print("\n[Step 3] Capturing payment...")
    print("This is when the merchant actually receives the funds.")
    response = requests.post(f"{BASE_URL}/payments/{payment_id}/capture")
    print_response("Payment Captured", response)

    payment = response.json()
    print(f"\nStatus: {payment['status']}")
    if payment['status'] == 'succeeded':
        print("Payment completed successfully!")
        print(f"Amount captured: ${payment['amount']/100:.2f}")
    else:
        print(f"Capture failed: {payment.get('error_message', 'Unknown error')}")

    time.sleep(1)

    # Step 4: View payment history
    print("\n[Step 4] Viewing payment event history...")
    response = requests.get(f"{BASE_URL}/payments/{payment_id}/events")
    print_response("Payment Events", response)

    events = response.json()
    print("\nPayment Timeline:")
    for event in events:
        print(f"  - {event['created_at']}: {event['event_type']} ({event['status']})")

    time.sleep(1)

    # Step 5: Refund the payment
    print("\n[Step 5] Creating refund...")
    refund_data = {
        "amount": 4999,  # Full refund
        "reason": "Customer requested refund"
    }
    response = requests.post(
        f"{BASE_URL}/payments/{payment_id}/refunds",
        json=refund_data
    )
    print_response("Refund Created", response)

    if response.status_code == 201:
        refund = response.json()
        print(f"\nRefund ID: {refund['id']}")
        print(f"Refund Status: {refund['status']}")
        print(f"Amount refunded: ${refund['amount']/100:.2f}")

    # Step 6: View final payment state
    print("\n[Step 6] Viewing final payment state...")
    response = requests.get(f"{BASE_URL}/payments/{payment_id}")
    print_response("Final Payment State", response)

    payment = response.json()
    print(f"\nFinal Status: {payment['status']}")

    print("\n" + "="*60)
    print("Example completed successfully!")
    print("="*60)


def test_declined_card():
    """Test with a card that will be declined"""
    print("\n\n" + "="*60)
    print("Testing Declined Card Scenario")
    print("="*60)

    payment_data = {
        "amount": 1000,
        "currency": "USD",
        "card": {
            "number": "4000000000000002",  # Test card that always declines
            "exp_month": 12,
            "exp_year": 2025,
            "cvc": "123"
        },
        "customer_email": "test@example.com",
        "description": "Test declined payment"
    }

    print("\nCreating payment with test declined card...")
    response = requests.post(f"{BASE_URL}/payments/", json=payment_data)
    print_response("Payment Created", response)

    if response.status_code == 201:
        payment = response.json()
        payment_id = payment["id"]

        print("\nAttempting to authorize...")
        response = requests.post(f"{BASE_URL}/payments/{payment_id}/authorize")
        print_response("Authorization Result", response)

        payment = response.json()
        if payment['status'] == 'failed':
            print(f"\nExpected failure: {payment['error_message']}")


def test_cancel():
    """Test cancelling an authorized payment"""
    print("\n\n" + "="*60)
    print("Testing Payment Cancellation")
    print("="*60)

    payment_data = {
        "amount": 5000,
        "currency": "USD",
        "card": {
            "number": "4242424242424242",
            "exp_month": 12,
            "exp_year": 2025,
            "cvc": "123"
        },
        "customer_email": "test@example.com",
        "description": "Test cancellation"
    }

    print("\nCreating and authorizing payment...")
    response = requests.post(f"{BASE_URL}/payments/", json=payment_data)
    payment = response.json()
    payment_id = payment["id"]

    response = requests.post(f"{BASE_URL}/payments/{payment_id}/authorize")
    payment = response.json()

    if payment['status'] == 'authorized':
        print(f"Payment authorized with code: {payment['authorization_code']}")

        print("\nCancelling payment...")
        response = requests.post(f"{BASE_URL}/payments/{payment_id}/cancel")
        print_response("Payment Cancelled", response)

        payment = response.json()
        print(f"\nFinal Status: {payment['status']}")
        print("Funds released back to customer!")


if __name__ == "__main__":
    try:
        # Run main example
        main()

        # Run additional test scenarios
        test_declined_card()
        test_cancel()

    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to API server.")
        print("Make sure the server is running with:")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\nError: {e}")
