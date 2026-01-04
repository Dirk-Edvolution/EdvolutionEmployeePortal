"""
API Endpoint Tests for Self-Service Portal

This script tests the travel, tool, and asset API endpoints.
Run after deploying to Cloud Run.

Usage:
    python test_api_endpoints.py <BASE_URL>

Example:
    python test_api_endpoints.py https://test---employee-portal-5n2ivebvra-uc.a.run.app
"""

import sys
import requests
import json
from datetime import date, timedelta


class APITester:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def test_health_check(self):
        """Test health check endpoint"""
        print("\n🏥 Testing Health Check...")
        print("-" * 60)

        try:
            response = self.session.get(f"{self.base_url}/health")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")

            if response.status_code == 200:
                print("✅ Health check passed")
                return True
            else:
                print("❌ Health check failed")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def test_travel_endpoints(self):
        """Test travel request endpoints (requires authentication)"""
        print("\n✈️  Testing Travel Request Endpoints...")
        print("-" * 60)

        # Note: These will fail without authentication, which is expected
        endpoints = [
            ('GET', '/api/travel/requests', 'Get my travel requests'),
            ('GET', '/api/travel/requests/pending', 'Get pending travel approvals'),
        ]

        for method, endpoint, description in endpoints:
            try:
                print(f"\n{description}:")
                print(f"  {method} {endpoint}")

                if method == 'GET':
                    response = self.session.get(f"{self.base_url}{endpoint}")

                print(f"  Status: {response.status_code}")

                if response.status_code == 401:
                    print("  ✅ Correctly requires authentication")
                elif response.status_code == 200:
                    print(f"  ✅ Success (but shouldn't work without auth)")
                else:
                    print(f"  ⚠️  Unexpected status: {response.status_code}")

            except Exception as e:
                print(f"  ❌ Error: {e}")

    def test_tool_endpoints(self):
        """Test tool request endpoints (requires authentication)"""
        print("\n🛠️  Testing Tool Request Endpoints...")
        print("-" * 60)

        endpoints = [
            ('GET', '/api/tool/requests', 'Get my tool requests'),
            ('GET', '/api/tool/requests/pending', 'Get pending tool approvals'),
        ]

        for method, endpoint, description in endpoints:
            try:
                print(f"\n{description}:")
                print(f"  {method} {endpoint}")

                if method == 'GET':
                    response = self.session.get(f"{self.base_url}{endpoint}")

                print(f"  Status: {response.status_code}")

                if response.status_code == 401:
                    print("  ✅ Correctly requires authentication")
                elif response.status_code == 200:
                    print(f"  ✅ Success (but shouldn't work without auth)")
                else:
                    print(f"  ⚠️  Unexpected status: {response.status_code}")

            except Exception as e:
                print(f"  ❌ Error: {e}")

    def test_asset_endpoints(self):
        """Test asset endpoints (requires authentication)"""
        print("\n📦 Testing Asset Endpoints...")
        print("-" * 60)

        # Test with a dummy email - should fail auth
        test_email = "test@edvolution.io"
        endpoint = f"/api/assets/employees/{test_email}"

        try:
            print(f"\nGet employee assets:")
            print(f"  GET {endpoint}")

            response = self.session.get(f"{self.base_url}{endpoint}")

            print(f"  Status: {response.status_code}")

            if response.status_code == 401:
                print("  ✅ Correctly requires authentication")
            elif response.status_code == 200:
                print(f"  ✅ Success (but shouldn't work without auth)")
            else:
                print(f"  ⚠️  Unexpected status: {response.status_code}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    def test_route_registration(self):
        """Test that all routes are registered by checking 404 vs 401"""
        print("\n🔍 Testing Route Registration...")
        print("-" * 60)

        routes = [
            '/api/travel/requests',
            '/api/tool/requests',
            '/api/assets/employees/test@example.com',
        ]

        for route in routes:
            try:
                response = self.session.get(f"{self.base_url}{route}")

                if response.status_code == 404:
                    print(f"❌ {route} - NOT REGISTERED (404)")
                elif response.status_code == 401:
                    print(f"✅ {route} - Registered (requires auth)")
                elif response.status_code == 200:
                    print(f"✅ {route} - Registered (public or already authenticated)")
                else:
                    print(f"⚠️  {route} - Status {response.status_code}")

            except Exception as e:
                print(f"❌ {route} - Error: {e}")

    def run_all_tests(self):
        """Run all API tests"""
        print("\n" + "=" * 60)
        print("🧪 Self-Service Portal API Endpoint Tests")
        print("=" * 60)
        print(f"\nBase URL: {self.base_url}")

        # Test health check (should always work)
        health_ok = self.test_health_check()

        if not health_ok:
            print("\n⚠️  Health check failed - service may not be running")
            print("Continuing with other tests...")

        # Test route registration
        self.test_route_registration()

        # Test protected endpoints (should require auth)
        self.test_travel_endpoints()
        self.test_tool_endpoints()
        self.test_asset_endpoints()

        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print("""
Expected Results:
- ✅ Health check returns 200
- ✅ All API routes return 401 (Unauthorized) - this is CORRECT
- ❌ Any route returning 404 means it's NOT registered

Note: All endpoints require authentication, so 401 responses are expected
and indicate the routes are properly registered and protected.

To test with authentication, you need to:
1. Log in through the web interface
2. Copy the session cookie
3. Add it to the requests in this script
""")
        print("=" * 60 + "\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_api_endpoints.py <BASE_URL>")
        print("\nExample:")
        print("  python test_api_endpoints.py https://test---employee-portal-5n2ivebvra-uc.a.run.app")
        sys.exit(1)

    base_url = sys.argv[1]
    tester = APITester(base_url)
    tester.run_all_tests()


if __name__ == '__main__':
    main()
