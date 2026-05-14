import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("TESTING DJANGO URL SHORTENER API")
print("=" * 60)

# Test 1: Create a shortened URL with custom code
print("\n1. Testing POST /shorten/ - Create shortened URL with custom code")
print("-" * 60)
payload1 = {
    "original_url": "https://www.google.com",
    "custom_code": "google"
}
try:
    response = requests.post(f"{BASE_URL}/shorten/", json=payload1)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    short_code_1 = response.json().get("short_code")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Create another shortened URL without custom code (auto-generated)
print("\n2. Testing POST /shorten/ - Create shortened URL (auto-generated code)")
print("-" * 60)
payload2 = {
    "original_url": "https://www.github.com"
}
try:
    response = requests.post(f"{BASE_URL}/shorten/", json=payload2)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    short_code_2 = response.json().get("short_code")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Get stats for first shortened URL
print("\n3. Testing GET /<short_code>/stats/ - Get URL statistics")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/google/stats/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Test redirect (this will follow the redirect)
print("\n4. Testing GET /<short_code>/ - Redirect to original URL")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/google/", allow_redirects=False)
    print(f"Status Code: {response.status_code}")
    print(f"Location Header: {response.headers.get('Location', 'N/A')}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

# Test 5: Get stats after redirect (should have incremented clicks)
print("\n5. Testing GET /<short_code>/stats/ - Check click count after redirect")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/google/stats/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

# Test 6: Test invalid short code
print("\n6. Testing GET /<invalid_code>/stats/ - Test 404 error handling")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/invalid123/stats/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("TESTING COMPLETE")
print("=" * 60)
