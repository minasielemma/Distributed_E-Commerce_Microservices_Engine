import os
import uuid
import hmac
import hashlib
import requests
import logging

logger = logging.getLogger(__name__)

class PolarPaymentProvider:
    def __init__(self):
        self.api_key = os.getenv("POLAR_API_KEY", "")
        self.webhook_secret = os.getenv("POLAR_WEBHOOK_SECRET", "")
        self.product_id = os.getenv("POLAR_PRODUCT_ID", "")
        self.organization_id = os.getenv("POLAR_ORGANIZATION_ID", "")
        self.is_sandbox = os.getenv("POLAR_ENVIRONMENT", "sandbox").lower() == "sandbox"
        
        # Polar Base API URLs
        if self.is_sandbox:
            self.base_url = "https://sandbox-api.polar.sh/v1"
        else:
            self.base_url = "https://api.polar.sh/v1"

    def update_polar_product_price(self, polar_product_id, new_price, name=None):
        """Updates the price (and optionally name) of an existing product in Polar API."""
        if not self.api_key or not polar_product_id:
            return False

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            amount_in_cents = int(float(new_price) * 100) if new_price else 1000
            if amount_in_cents <= 0:
                amount_in_cents = 1000

            patch_payload = {
                "prices": [{
                    "amount_type": "fixed",
                    "price_amount": amount_in_cents,
                    "price_currency": "usd"
                }]
            }
            if name:
                patch_payload["name"] = name

            res = requests.patch(f"{self.base_url}/products/{polar_product_id}", headers=headers, json=patch_payload, timeout=8)
            if res.status_code in [200, 201]:
                logger.info(f"Successfully updated price for Polar product {polar_product_id} to ${new_price}")
                return True
            else:
                logger.error(f"Failed to update Polar product price ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Exception during Polar product price update: {e}")

        return False

    def ensure_polar_product_price_matches(self, polar_product_id, target_price, name=None):
        """
        Checks if the price of an existing Polar product matches the local product price.
        If it differs, updates the Polar product price automatically.
        """
        if not self.api_key or not polar_product_id or target_price is None:
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            expected_cents = int(float(target_price) * 100)
            if expected_cents <= 0:
                return

            res = requests.get(f"{self.base_url}/products/{polar_product_id}", headers=headers, timeout=5)
            if res.status_code == 200:
                prod = res.json()
                prices = prod.get("prices", [])
                current_price_amount = None
                if prices:
                    current_price_amount = prices[0].get("price_amount")

                if current_price_amount != expected_cents:
                    logger.info(f"Price mismatch for Polar product {polar_product_id}: local is {expected_cents} cents, Polar is {current_price_amount} cents. Updating Polar product price...")
                    self.update_polar_product_price(polar_product_id, target_price, name=name)
        except Exception as e:
            logger.warning(f"Could not verify/sync Polar product price for {polar_product_id}: {e}")

    def sync_product_to_polar(self, product_id, name, price, description="", existing_polar_id=None):
        if not self.api_key or self.api_key in ["polar_test_key_sample", ""]:
            return None

        if existing_polar_id:
            self.ensure_polar_product_price_matches(existing_polar_id, price, name=name)
            return existing_polar_id

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            amount_in_cents = int(float(price) * 100) if price else 1000
            if amount_in_cents <= 0:
                amount_in_cents = 1000

            product_payload = {
                "name": name or f"Product #{product_id}",
                "description": description or f"Catalog Product {product_id}",
                "prices": [{
                    "amount_type": "fixed",
                    "price_amount": amount_in_cents,
                    "price_currency": "usd"
                }]
            }

            create_res = requests.post(f"{self.base_url}/products/", headers=headers, json=product_payload, timeout=8)
            if create_res.status_code in [200, 201]:
                polar_id = create_res.json().get("id")
                logger.info(f"Successfully synced product {product_id} to Polar -> Polar ID: {polar_id}")

                # Update catalog service with generated polar_product_id
                if product_id:
                    try:
                        from payments.grpc_client import get_product_polar_id_grpc
                        get_product_polar_id_grpc(product_id)
                    except Exception as cat_err:
                        logger.warning(f"Could not check polar_product_id in catalog service via gRPC: {cat_err}")


                return polar_id
            else:
                logger.error(f"Failed to create product in Polar ({create_res.status_code}): {create_res.text}")
        except Exception as e:
            logger.error(f"Exception during Polar product sync: {e}")

        return None

    def _get_or_create_product_id(self, headers, catalog_product_id=None, product_name=None, amount=None):
        # 1. If explicit POLAR_PRODUCT_ID is set in environment variable
        env_product_id = os.getenv("POLAR_PRODUCT_ID", "").strip()
        if env_product_id:
            return env_product_id

        p_name = product_name
        p_price = amount

        # 2. Try fetching from catalog_service if product_id is provided
        if catalog_product_id:
            try:
                from payments.grpc_client import get_catalog_product
                prod_data = get_catalog_product(catalog_product_id)
                if prod_data and prod_data.found:
                    existing_polar_id = prod_data.polar_id
                    
                    if not p_name:
                        p_name = prod_data.get("name")
                    if not p_price or float(p_price) == 0:
                        p_price = prod_data.get("dynamic_price") or prod_data.get("base_price")

                    if existing_polar_id:
                        # Ensure local price and polar product price match!
                        self.ensure_polar_product_price_matches(existing_polar_id, p_price, name=p_name)
                        return existing_polar_id
            except Exception as e:
                logger.warning(f"Could not fetch product from catalog_service: {e}")

        # 3. Create or sync product to Polar with exact product name and price
        target_name = p_name or (f"Product #{catalog_product_id}" if catalog_product_id else "Order Checkout")
        target_price = p_price or 10.00

        synced_id = self.sync_product_to_polar(catalog_product_id, target_name, target_price)
        if synced_id:
            return synced_id

        return None

    def create_checkout_session(self, order_id, customer_id, amount, catalog_product_id=None, polar_product_id=None, product_name=None):
        if self.api_key and self.api_key not in ["polar_test_key_sample", ""]:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                target_polar_product_id = polar_product_id or self._get_or_create_product_id(
                    headers, 
                    catalog_product_id=catalog_product_id, 
                    product_name=product_name, 
                    amount=amount
                )
                
                amount_in_cents = int(float(amount) * 100)
                success_url = os.getenv(
                    "POLAR_SUCCESS_URL", 
                    f"http://localhost/checkout/success?order_id={order_id}"
                )
                
                payload = {
                    "success_url": success_url,
                    "amount": amount_in_cents,
                    "metadata": {
                        "order_id": str(order_id),
                        "customer_id": str(customer_id)
                    }
                }

                if target_polar_product_id:
                    payload["product_id"] = target_polar_product_id

                # Call Polar API to create a checkout session
                response = requests.post(
                    f"{self.base_url}/checkouts/custom/",
                    headers=headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code in [200, 201]:
                    res_data = response.json()
                    logger.info(f"Polar checkout session created successfully: {res_data.get('url')}")
                    return {
                        "checkout_id": res_data.get("id"),
                        "checkout_url": res_data.get("url"),
                        "polar_product_id": target_polar_product_id
                    }
                else:
                    err_msg = f"Polar API checkout error ({response.status_code}): {response.text}"
                    logger.error(err_msg)
                    return {
                        "error": f"Polar API error ({response.status_code})",
                        "details": response.text
                    }
            except Exception as e:
                logger.error(f"Error calling Polar API: {e}")
                return {
                    "error": "Failed to connect to Polar API",
                    "details": str(e)
                }

        return {
            "error": "POLAR_API_KEY is not configured",
            "details": "Please set a valid POLAR_API_KEY in payment_service/.env"
        }



    def verify_webhook_signature(self, payload_bytes, signature_header, msg_id=None, msg_timestamp=None):
        import base64
        if not self.webhook_secret or self.webhook_secret.strip() in ['', 'whsec_test', 'sample_secret']:
            return True

        if not signature_header:
            logger.warning("No webhook signature header provided in request.")
            if self.is_sandbox:
                logger.info("Sandbox mode: allowing webhook request without signature header.")
                return True
            return False

        secret_str = self.webhook_secret.strip()
        possible_secrets = []
        if secret_str.startswith('whsec_'):
            try:
                possible_secrets.append(base64.b64decode(secret_str[6:]))
            except Exception:
                pass
            possible_secrets.append(secret_str[6:].encode('utf-8'))
        possible_secrets.append(secret_str.encode('utf-8'))

        target_sigs = []
        for item in signature_header.strip().split():
            if ',' in item:
                target_sigs.append(item.split(',', 1)[-1])
            elif '=' in item:
                target_sigs.append(item.split('=', 1)[-1])
            else:
                target_sigs.append(item)

        for sec in possible_secrets:
            # 1. Standard Webhooks signature verification (Polar standard)
            if msg_id and msg_timestamp:
                try:
                    to_sign = f"{msg_id}.{msg_timestamp}.".encode('utf-8') + payload_bytes
                    computed_b64 = base64.b64encode(hmac.new(sec, to_sign, hashlib.sha256).digest()).decode('utf-8')
                    computed_hex = hmac.new(sec, to_sign, hashlib.sha256).hexdigest()
                    
                    for sig_val in target_sigs:
                        if hmac.compare_digest(computed_b64, sig_val) or hmac.compare_digest(computed_hex, sig_val):
                            logger.info("Polar webhook signature verified successfully (Standard Webhooks format).")
                            return True
                except Exception as err:
                    logger.warning(f"Standard Webhooks signature calculation error: {err}")

            # 2. Simple HMAC-SHA256 signature verification (payload directly)
            try:
                computed_hex = hmac.new(sec, payload_bytes, hashlib.sha256).hexdigest()
                computed_b64 = base64.b64encode(hmac.new(sec, payload_bytes, hashlib.sha256).digest()).decode('utf-8')

                for sig_val in target_sigs:
                    if hmac.compare_digest(computed_hex, sig_val) or hmac.compare_digest(computed_b64, sig_val):
                        logger.info("Polar webhook signature verified successfully (Direct HMAC format).")
                        return True
            except Exception as err:
                logger.warning(f"HMAC signature calculation error: {err}")

        # 3. Fallback for sandbox/testing
        if self.is_sandbox:
            logger.info(f"Webhook signature processed under sandbox mode.")
            return True

        return False


