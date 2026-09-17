import requests
import json

BASE_URL = "http://localhost:8080/api"

def test_polar_checkout_url():
    print("\n--- Testing Official Polar Payment Checkout URL ---")
    username = "testcustomer1"
    password = "password123!"

    login_resp = requests.post(f"{BASE_URL}/auth/token/", json={
        "username": username,
        "password": password
    })
    token = login_resp.json()["access"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    cat_resp = requests.get(f"{BASE_URL}/catalog/products/")
    products = cat_resp.json().get("results", [])
    prod = products[0]

    order_payload = {
        "items": [{
            "product_id": prod["id"],
            "product_name": prod["name"],
            "unit_price": float(prod.get("base_price") or 19.99),
            "quantity": 1,
            "tenant_id": prod.get("tenant_id")
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
        "shipping_cost": 0,
        "tax_amount": 0
    }

    create_resp = requests.post(f"{BASE_URL}/orders/create/", json=order_payload, headers=headers)
    assert create_resp.status_code in (200, 201), f"Order creation failed: {create_resp.text}"
    order_id = create_resp.json()["order"]["id"]
    print("Order created with ID:", order_id)

    pay_resp = requests.post(f"{BASE_URL}/orders/{order_id}/pay/", json={}, headers=headers)
    assert pay_resp.status_code == 200, f"Pay order failed: {pay_resp.text}"
    pay_data = pay_resp.json()
    checkout_url = pay_data.get("payment", {}).get("checkout_url") or pay_data.get("checkout_url")
    print("Generated Official Polar Checkout URL:", checkout_url)

    assert checkout_url.startswith("https://sandbox.polar.sh/checkout/") or checkout_url.startswith("https://polar.sh/checkout/"), f"Invalid Polar checkout URL: {checkout_url}"
    print("Official Polar Checkout URL verification PASSED!")

def test_local_image_upload_and_storage():
    print("\n--- Testing Local Image Upload & Machine Host Storage ---")
    username = "testcustomer1"
    password = "password123!"

    login_resp = requests.post(f"{BASE_URL}/auth/token/", json={
        "username": username,
        "password": password
    })
    token = login_resp.json()["access"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    sample_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
        b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
        b"\xe5\x27\xde\xfc\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    files = {"file": ("test_upload.png", sample_png, "image/png")}
    data = {"visibility": "PUBLIC"}

    upload_resp = requests.post(f"{BASE_URL}/media/upload/", files=files, data=data, headers=auth_headers)
    print("Upload Status:", upload_resp.status_code)
    assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
    file_url = upload_resp.json()["file_url"]
    print("Uploaded File URL:", file_url)

    full_img_url = f"http://localhost:8080{file_url}"
    img_resp = requests.get(full_img_url)
    print("Inline Image Fetch Status:", img_resp.status_code)
    print("Content-Type:", img_resp.headers.get("Content-Type"))
    print("Content-Disposition:", img_resp.headers.get("Content-Disposition"))

    assert img_resp.status_code == 200, f"Image fetch failed: {img_resp.status_code}"
    assert "image" in img_resp.headers.get("Content-Type", "").lower(), "Content-Type should be image!"
    assert "inline" in img_resp.headers.get("Content-Disposition", "").lower(), "Content-Disposition should be inline!"
    print("Local image upload & host persistent serving PASSED!")

if __name__ == "__main__":
    test_polar_checkout_url()
    test_local_image_upload_and_storage()
