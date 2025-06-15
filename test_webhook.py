import requests
import json

# Test the webhook endpoint
def test_webhook():
    url = "http://localhost:8000/webhook/"
    
    # Test data
    data = {
        "message": {
            "text": "Hello, how are you?"
        },
        "user": {
            "id": "test_user_123"
        }
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_webhook() 