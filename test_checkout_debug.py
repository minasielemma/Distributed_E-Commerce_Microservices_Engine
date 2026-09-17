import requests
import json

BASE_URL = "http://localhost:8080/api"

def run_test():
    username = "testcustomer1"
    password = "password123!"

    print("Logging in...")
    login_resp = requests.post(f"{BASE_URL}/auth/token/", json={
        "username": username,
        "password": password
    })
    token = login_resp.json()["access"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print("Fetching product from catalog...")
    cat_resp = requests.get(f"{BASE_URL}/catalog/products/")
    data = cat_resp.json()
    products = data.get("results", data if isinstance(data, list) else [])
    if not products:
        print("No products found!")
        return
    prod = products[0]
    print("Product structure keys:", list(prod.keys()))
    print("Sample product:", json.dumps(prod, indent=2))

    prod_id = prod["id"]
    tenant_id = prod.get("tenant_id")
    prod_name = prod.get("name") or prod.get("title") or "Test Product"

    print("Creating order...")
    order_payload = {
        "items": [{
            "product_id": prod_id,
            "product_name": prod_name,
            "unit_price": float(prod.get("price") or 19.99),
            "quantity": 1,
            "tenant_id": tenant_id
        }],
        "shipping_address": {
            "full_name": "Test Customer",
            "address_line_1": "123 Main St",
            "city": "Addis Ababa",
            "state": "AA",
            "postal_code": "1000",
            "country": "Ethiopia",
            "phone_number": "+251911000000"
        },
        "billing_address": {
            "full_name": "Test Customer",
            "address_line_1": "123 Main St",
            "city": "Addis Ababa",
            "state": "AA",
            "postal_code": "1000",
            "country": "Ethiopia",
            "phone_number": "+251911000000"
        },
        "shipping_cost": 0,
        "tax_amount": 0
    }

    create_resp = requests.post(f"{BASE_URL}/orders/create/", json=order_payload, headers=headers)
    print("Create Order status:", create_resp.status_code)
    print("Create Order response:", create_resp.text)

    if create_resp.status_code not in (200, 201):
        return

    order_data = create_resp.json().get("order", {})
    order_id = order_data.get("id")
    print(f"Order created with ID: {order_id}")

    print("Initiating payment...")
    pay_resp = requests.post(f"{BASE_URL}/orders/{order_id}/pay/", json={}, headers=headers)
    print("Pay status:", pay_resp.status_code)
    print("Pay response:", pay_resp.text)

if __name__ == "__main__":
    run_test()
