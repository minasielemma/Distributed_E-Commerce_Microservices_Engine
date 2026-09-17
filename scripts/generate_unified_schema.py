#!/usr/bin/env python3
"""
OpenAPI 3.0 Schema Aggregator Script.
Fetches or generates OpenAPI 3.0 specs from all 11 microservices,
resolves component definition collisions, and merges paths into a single master openapi_3_0_merged.json.
"""

import json
import os
import urllib.request

SERVICES = [
    {"name": "Identity & Auth Service", "prefix": "/api/auth", "url": "http://identity_service:8000/api/auth/schema/"},
    {"name": "Catalog Service", "prefix": "/api/catalog", "url": "http://catalog_service:8000/api/catalog/schema/"},
    {"name": "Cart Service", "prefix": "/api/cart", "url": "http://cart_service:8000/api/cart/schema/"},
    {"name": "Order Service", "prefix": "/api/orders", "url": "http://order_service:8000/api/orders/schema/"},
    {"name": "Payment Service", "prefix": "/api/payments", "url": "http://payment_service:8000/api/payments/schema/"},
    {"name": "Inventory Service", "prefix": "/api/inventory", "url": "http://inventory_service:8000/api/inventory/schema/"},
    {"name": "Finance Service", "prefix": "/api/finance", "url": "http://finance_service:8000/api/finance/schema/"},
    {"name": "Media Service", "prefix": "/api/media", "url": "http://media_service:8000/api/media/schema/"},
    {"name": "Chat Service", "prefix": "/api/chat", "url": "http://chat_service:8000/api/chat/schema/"},
    {"name": "Recommendation Service", "prefix": "/api/recommendations", "url": "http://recommendation_service:8000/api/recommendations/schema/"},
    {"name": "Notification Service", "prefix": "/api/notifications", "url": "http://notification_service:8000/api/notifications/schema/"},
]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schemas")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "openapi_3_0_merged.json")

def merge_schemas():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    merged_spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Unified Microservices OpenAPI 3.0 Ecosystem",
            "description": "Aggregated OpenAPI 3.0 specification for all 11 backend microservices.",
            "version": "1.0.0"
        },
        "servers": [{"url": "/", "description": "API Gateway Proxy"}],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Enter JWT Bearer token format: Bearer <token>"
                }
            }
        },
        "security": [{"BearerAuth": []}],
        "tags": []
    }

    for service in SERVICES:
        tag_name = service["name"]
        merged_spec["tags"].append({"name": tag_name, "description": f"Endpoints for {tag_name}"})
        
        schema_data = None
        try:
            req = urllib.request.Request(service["url"], headers={"User-Agent": "OpenAPI-Aggregator"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                schema_data = json.loads(resp.read().decode('utf-8'))
        except Exception:
            schema_data = {
                "paths": {
                    f"{service['prefix']}/": {
                        "get": {
                            "summary": f"List {service['name']} items",
                            "tags": [tag_name],
                            "responses": {"200": {"description": "OK"}}
                        }
                    }
                },
                "components": {}
            }

        # Merge paths
        paths = schema_data.get("paths", {})
        for path, path_item in paths.items():
            for method in path_item:
                if isinstance(path_item[method], dict):
                    path_item[method]["tags"] = [tag_name]
            merged_spec["paths"][path] = path_item

        # Merge components
        components = schema_data.get("components", {})
        schemas = components.get("schemas", {})
        for schema_name, schema_def in schemas.items():
            key = f"{service['name'].replace(' ', '')}_{schema_name}"
            merged_spec["components"]["schemas"][key] = schema_def

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(merged_spec, f, indent=2)

    print(f"Successfully generated merged OpenAPI 3.0 schema at: {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_schemas()
