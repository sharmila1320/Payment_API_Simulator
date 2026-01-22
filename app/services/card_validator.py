import re
from datetime import datetime


def luhn_check(card_number: str) -> bool:
    """
    Validate card number using Luhn algorithm (mod 10)
    This is how real payment processors validate card numbers
    """
    def digits_of(n):
        return [int(d) for d in str(n)]

    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]

    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))

    return checksum % 10 == 0


def get_card_brand(card_number: str) -> str:
    """Identify card brand from number"""
    card_number = re.sub(r'[\s-]', '', card_number)

    # Card brand patterns
    patterns = {
        'card': r'^4',
        'mastercard': r'^5[1-5]|^2[2-7]',
        'amex': r'^3[47]',
        'discover': r'^6(?:011|5)',
        'jcb': r'^35',
    }

    for brand, pattern in patterns.items():
        if re.match(pattern, card_number):
            return brand

    return 'unknown'


def validate_card(card_number: str, exp_month: int, exp_year: int, cvc: str) -> tuple[bool, str]:
    """
    Comprehensive card validation
    Returns (is_valid, error_message)
    """
    # Remove spaces and dashes
    card_number = re.sub(r'[\s-]', '', card_number)

    # Check length
    if len(card_number) not in [15, 16]:
        return False, "Invalid card number length"

    # Check if all digits
    if not card_number.isdigit():
        return False, "Card number must contain only digits"

    # Luhn check
    if not luhn_check(card_number):
        return False, "Invalid card number"

    # Check expiration
    now = datetime.now()
    if exp_year < now.year or (exp_year == now.year and exp_month < now.month):
        return False, "Card has expired"

    # Check CVC
    if not cvc.isdigit() or len(cvc) not in [3, 4]:
        return False, "Invalid CVC"

    # Test card numbers (always decline)
    test_declined_cards = ['4000000000000002', '4000000000009995']
    if card_number in test_declined_cards:
        return False, "Card declined by issuer"

    return True, ""


def mask_card_number(card_number: str) -> str:
    """Mask card number, showing only last 4 digits"""
    card_number = re.sub(r'[\s-]', '', card_number)
    return '*' * (len(card_number) - 4) + card_number[-4:]
