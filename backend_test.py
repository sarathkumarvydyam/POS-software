#!/usr/bin/env python3
"""
Urban Bites MVP Backend API Tests
Tests all backend endpoints sequentially as specified in the review request.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Load backend URL from frontend .env
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
        return None
    return None

BASE_URL = get_backend_url()
if not BASE_URL:
    print("ERROR: Could not find REACT_APP_BACKEND_URL in frontend/.env")
    sys.exit(1)

print(f"Testing Urban Bites API at: {BASE_URL}")

# Test results tracking
test_results = []
failed_tests = []

def log_test(test_name: str, success: bool, details: str = ""):
    """Log test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")
    
    test_results.append({
        "test": test_name,
        "success": success,
        "details": details
    })
    
    if not success:
        failed_tests.append(test_name)

def test_config_public():
    """Test GET /api/config/public"""
    try:
        response = requests.get(f"{BASE_URL}/api/config/public", timeout=10)
        
        if response.status_code != 200:
            log_test("Config Public API", False, f"Status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        
        # Check required fields
        required_fields = ['brand', 'currency', 'tax_rate', 'payments_enabled', 'hero_image']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            log_test("Config Public API", False, f"Missing fields: {missing_fields}")
            return None
            
        # Validate field types and values
        if not isinstance(data['brand'], dict):
            log_test("Config Public API", False, "brand should be a dict")
            return None
            
        if data['currency'] != 'USD':
            log_test("Config Public API", False, f"Expected currency USD, got {data['currency']}")
            return None
            
        if not isinstance(data['tax_rate'], (int, float)):
            log_test("Config Public API", False, "tax_rate should be numeric")
            return None
            
        if not isinstance(data['payments_enabled'], bool):
            log_test("Config Public API", False, "payments_enabled should be boolean")
            return None
            
        if not isinstance(data['hero_image'], dict) or 'url' not in data['hero_image']:
            log_test("Config Public API", False, "hero_image should be dict with url")
            return None
            
        log_test("Config Public API", True, f"Got config with brand: {data['brand'].get('name', 'N/A')}")
        return data
        
    except Exception as e:
        log_test("Config Public API", False, f"Exception: {str(e)}")
        return None

def test_menu_categories():
    """Test GET /api/menu/categories"""
    try:
        response = requests.get(f"{BASE_URL}/api/menu/categories", timeout=10)
        
        if response.status_code != 200:
            log_test("Menu Categories API", False, f"Status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        
        if not isinstance(data, list):
            log_test("Menu Categories API", False, "Response should be a list")
            return None
            
        if len(data) == 0:
            log_test("Menu Categories API", False, "Categories list is empty")
            return None
            
        # Check each category has required fields
        for category in data:
            if not isinstance(category, dict):
                log_test("Menu Categories API", False, "Each category should be a dict")
                return None
            if 'slug' not in category or 'name' not in category:
                log_test("Menu Categories API", False, "Each category should have slug and name")
                return None
                
        log_test("Menu Categories API", True, f"Got {len(data)} categories: {[c['slug'] for c in data]}")
        return data
        
    except Exception as e:
        log_test("Menu Categories API", False, f"Exception: {str(e)}")
        return None

def test_menu_products():
    """Test GET /api/menu/products?category=burgers"""
    try:
        response = requests.get(f"{BASE_URL}/api/menu/products?category=burgers", timeout=10)
        
        if response.status_code != 200:
            log_test("Menu Products API", False, f"Status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        
        if not isinstance(data, list):
            log_test("Menu Products API", False, "Response should be a list")
            return None
            
        if len(data) == 0:
            log_test("Menu Products API", False, "Products list is empty for category=burgers")
            return None
            
        # Check each product has required fields
        required_fields = ['product_id', 'name', 'base_price', 'images', 'variants', 'add_ons']
        for product in data:
            if not isinstance(product, dict):
                log_test("Menu Products API", False, "Each product should be a dict")
                return None
                
            missing_fields = [field for field in required_fields if field not in product]
            if missing_fields:
                log_test("Menu Products API", False, f"Product missing fields: {missing_fields}")
                return None
                
            # Validate field types
            if not isinstance(product['base_price'], (int, float)):
                log_test("Menu Products API", False, "base_price should be numeric")
                return None
                
            if not isinstance(product['images'], list):
                log_test("Menu Products API", False, "images should be a list")
                return None
                
            if not isinstance(product['variants'], list):
                log_test("Menu Products API", False, "variants should be a list")
                return None
                
            if not isinstance(product['add_ons'], list):
                log_test("Menu Products API", False, "add_ons should be a list")
                return None
                
        log_test("Menu Products API", True, f"Got {len(data)} burger products")
        return data
        
    except Exception as e:
        log_test("Menu Products API", False, f"Exception: {str(e)}")
        return None

def test_validate_coupon():
    """Test POST /api/cart/validate-coupon"""
    try:
        payload = {
            "code": "URBAN10",
            "subtotal": 30.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/cart/validate-coupon", 
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_test("Validate Coupon API", False, f"Status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        
        # Check required fields
        required_fields = ['discount_type', 'discount_amount']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            log_test("Validate Coupon API", False, f"Missing fields: {missing_fields}")
            return None
            
        # Validate values
        if data['discount_type'] != 'percent':
            log_test("Validate Coupon API", False, f"Expected discount_type 'percent', got {data['discount_type']}")
            return None
            
        expected_discount = 3.0  # 10% of 30
        if abs(data['discount_amount'] - expected_discount) > 0.01:
            log_test("Validate Coupon API", False, f"Expected discount_amount {expected_discount}, got {data['discount_amount']}")
            return None
            
        log_test("Validate Coupon API", True, f"URBAN10 coupon validated: {data['discount_amount']} discount")
        return data
        
    except Exception as e:
        log_test("Validate Coupon API", False, f"Exception: {str(e)}")
        return None

def test_create_order(products_data):
    """Test POST /api/orders/"""
    if not products_data or len(products_data) == 0:
        log_test("Create Order API", False, "No products available for order creation")
        return None
        
    try:
        # Use first product for order
        product = products_data[0]
        variant_id = product['variants'][0]['variant_id'] if product['variants'] else None
        
        payload = {
            "items": [
                {
                    "product_id": product['product_id'],
                    "variant_id": variant_id,
                    "quantity": 2,
                    "add_on_ids": []
                }
            ],
            "user": {
                "name": "John Smith",
                "email": "john.smith@example.com"
            },
            "fulfillment_type": "pickup",
            "tip_amount": 2.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/orders/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code != 200:
            log_test("Create Order API", False, f"Status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        
        # Check required fields
        required_fields = ['order_id', 'totals']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            log_test("Create Order API", False, f"Missing fields: {missing_fields}")
            return None
            
        # Validate totals structure
        if not isinstance(data['totals'], dict):
            log_test("Create Order API", False, "totals should be a dict")
            return None
            
        totals_fields = ['subtotal', 'tax_amount', 'tip_amount', 'total']
        missing_totals = [field for field in totals_fields if field not in data['totals']]
        
        if missing_totals:
            log_test("Create Order API", False, f"Missing totals fields: {missing_totals}")
            return None
            
        log_test("Create Order API", True, f"Order created: {data['order_id']}, total: ${data['totals']['total']}")
        return data
        
    except Exception as e:
        log_test("Create Order API", False, f"Exception: {str(e)}")
        return None

def test_get_order(order_data):
    """Test GET /api/orders/{order_id}"""
    if not order_data or 'order_id' not in order_data:
        log_test("Get Order API", False, "No order_id available for retrieval test")
        return None
        
    try:
        order_id = order_data['order_id']
        response = requests.get(f"{BASE_URL}/api/orders/{order_id}", timeout=10)
        
        if response.status_code != 200:
            log_test("Get Order API", False, f"Status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        
        # Check required fields
        required_fields = ['order_id', 'totals', 'user_info', 'order_status']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            log_test("Get Order API", False, f"Missing fields: {missing_fields}")
            return None
            
        # Verify order_id matches
        if data['order_id'] != order_id:
            log_test("Get Order API", False, f"Order ID mismatch: expected {order_id}, got {data['order_id']}")
            return None
            
        # Verify totals match original order
        original_totals = order_data['totals']
        retrieved_totals = data['totals']
        
        for field in ['subtotal', 'tax_amount', 'tip_amount', 'total']:
            if abs(retrieved_totals.get(field, 0) - original_totals.get(field, 0)) > 0.01:
                log_test("Get Order API", False, f"Totals mismatch for {field}: expected {original_totals.get(field)}, got {retrieved_totals.get(field)}")
                return None
                
        log_test("Get Order API", True, f"Order retrieved successfully: {order_id}")
        return data
        
    except Exception as e:
        log_test("Get Order API", False, f"Exception: {str(e)}")
        return None

def main():
    """Run all tests sequentially"""
    print("=" * 60)
    print("URBAN BITES MVP BACKEND API TESTS")
    print("=" * 60)
    
    # Test 1: Config public
    config_data = test_config_public()
    
    # Test 2: Menu categories
    categories_data = test_menu_categories()
    
    # Test 3: Menu products
    products_data = test_menu_products()
    
    # Test 4: Validate coupon
    coupon_data = test_validate_coupon()
    
    # Test 5: Create order
    order_data = test_create_order(products_data)
    
    # Test 6: Get order
    retrieved_order = test_get_order(order_data)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result['success'])
    failed_count = len(failed_tests)
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_count}")
    
    if failed_tests:
        print(f"\nFailed Tests:")
        for test in failed_tests:
            print(f"  - {test}")
    
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if failed_count == 0 else '❌ SOME TESTS FAILED'}")
    
    return failed_count == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)