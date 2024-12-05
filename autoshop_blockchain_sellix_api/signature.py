import hmac
import hashlib

# Define the secret and request body
WEBHOOK_SECRET = 'ECnDCfdDYsdnZrtBwgySWuPg1WmheYzX'
REQUEST_BODY = '{"order_id": "123456", "email": "customer@example.com", "amount": "50.00", "currency": "USD"}'

# Compute the signature
computed_signature = hmac.new(
    WEBHOOK_SECRET.encode(), 
    REQUEST_BODY.encode(), 
    hashlib.sha256
).hexdigest()

print(f"Computed Signature: {computed_signature}")
