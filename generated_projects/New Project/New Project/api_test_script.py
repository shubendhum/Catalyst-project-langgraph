import httpx
import json


API_URL = "http://localhost:8000"  # Change this to your API base URL
BEARER_TOKEN = "your_token_here"  # Replace with your actual token


def test_post_greet():
    print("Testing POST /api/greet...")

    # Valid request
    valid_data = {"name": "Alice"}
    response = httpx.post(f"{API_URL}/api/greet", json=valid_data, headers={"Authorization": f"Bearer {BEARER_TOKEN}"})
    
    # Check response of valid case
    if response.status_code == 200:
        print("Success:", response.json())
    else:
        print("Failed:", response.status_code, response.text)

    # Test missing name
    invalid_data_missing_name = {}
    response = httpx.post(f"{API_URL}/api/greet", json=invalid_data_missing_name, headers={"Authorization": f"Bearer {BEARER_TOKEN}"})
    
    if response.status_code == 400:
        print("Bad Request (missing name):", response.text)
    else:
        print("Unexpected Status:", response.status_code)

    # Test unauthorized access
    response = httpx.post(f"{API_URL}/api/greet", json={"name": "Alice"}, headers={"Authorization": "Bearer wrong_token"})
    
    if response.status_code == 401:
        print("Unauthorized (wrong token):", response.text)
    else:
        print("Unexpected Status:", response.status_code)


def test_get_greet():
    print("Testing GET /api/greet...")

    # Valid request
    response = httpx.get(f"{API_URL}/api/greet", headers={"Authorization": f"Bearer {BEARER_TOKEN}"})
    
    if response.status_code == 200:
        print("Success:", response.json())
    else:
        print("Failed:", response.status_code, response.text)

    # Test unauthorized access
    response = httpx.get(f"{API_URL}/api/greet", headers={"Authorization": "Bearer wrong_token"})
    
    if response.status_code == 401:
        print("Unauthorized (wrong token):", response.text)
    else:
        print("Unexpected Status:", response.status_code)


def main():
    print("Starting API tests...")
    test_results = {
        "POST /api/greet": {
            "success": [],
            "failures": []
        },
        "GET /api/greet": {
            "success": [],
            "failures": []
        }
    }
    
    # Capture POST test results
    try:
        test_post_greet()
        test_results["POST /api/greet"]["success"].append("Valid data test passed.")
    except Exception as e:
        test_results["POST /api/greet"]["failures"].append(str(e))

    # Capture GET test results
    try:
        test_get_greet()
        test_results["GET /api/greet"]["success"].append("Valid data test passed.")
    except Exception as e:
        test_results["GET /api/greet"]["failures"].append(str(e))

    # Print the summary
    print("Test Summary:")
    print(json.dumps(test_results, indent=2))


if __name__ == "__main__":
    main()