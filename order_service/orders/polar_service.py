import os
import uuid
import hmac
import hashlib

class PolarPaymentService:
    def __init__(self, is_sandbox=None):
        self.api_key = os.getenv("POLAR_API_KEY", "")
        self.webhook_secret = os.getenv("POLAR_WEBHOOK_SECRET", "")
        if is_sandbox is not None:
            self.is_sandbox = is_sandbox
        else:
            self.is_sandbox = os.getenv("POLAR_ENVIRONMENT", "sandbox").lower() == "sandbox"
        
        env_checkout = os.getenv("POLAR_CHECKOUT_BASE_URL", "").strip()
        if env_checkout:
            self.checkout_base_url = env_checkout.rstrip("/")
        else:
            self.checkout_base_url = "https://sandbox.polar.sh/checkout" if self.is_sandbox else "https://polar.sh/checkout"

    def create_checkout_session(self, order):
        checkout_id = f"polar_chk_{uuid.uuid4().hex[:12]}"
        checkout_url = f"{self.checkout_base_url}/{checkout_id}?order_id={order.id}&amount={order.total_amount}"

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
