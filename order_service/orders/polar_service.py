import os
import uuid
import hmac
import hashlib

class PolarPaymentService:
    def __init__(self):
        self.api_key = os.getenv("POLAR_API_KEY", "polar_test_key_sample")
        self.webhook_secret = os.getenv("POLAR_WEBHOOK_SECRET", "polar_whsec_sample")

    def create_checkout_session(self, order):
        checkout_id = f"polar_chk_{uuid.uuid4().hex[:12]}"
        checkout_url = f"https://polar.sh/checkout/{checkout_id}?order_id={order.id}&amount={order.total_amount}"

        return {
            "checkout_id": checkout_id,
            "checkout_url": checkout_url
        }

    def verify_webhook_signature(self, payload_bytes, signature_header):
        if not signature_header:
            return True

        expected_sig = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature_header)
