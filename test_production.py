#!/usr/bin/env python3
"""
Production QA Test Suite for Employee Portal
Tests: rrhh.edvolution.io
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys

BASE_URL = "https://rrhh.edvolution.io"

class ProductionTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_email = "dirk@edvolution.io"
        self.manager_email = "test@edvolution.io"

    def log_test(self, test_name: str, passed: bool, details: str = "", error: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "passed": passed,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "error": error
        }
        self.test_results.append(result)
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"  Details: {details}")
        if error:
            print(f"  Error: {error}")
        print()

    def test_site_accessibility(self):
        """Test 1: Site is accessible and returns valid HTML"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            passed = response.status_code == 200 and "Employee Portal" in response.text
            self.log_test(
                "Site Accessibility",
                passed,
                f"Status: {response.status_code}, Load time: {response.elapsed.total_seconds():.2f}s"
            )
            return passed
        except Exception as e:
            self.log_test("Site Accessibility", False, error=str(e))
            return False

    def test_oauth_redirect(self):
        """Test 2: OAuth login redirects correctly with client_id"""
        try:
            response = self.session.get(f"{BASE_URL}/auth/login", allow_redirects=False)
            location = response.headers.get('Location', '')
            has_client_id = 'client_id=' in location
            has_redirect_uri = 'redirect_uri=' in location
            passed = response.status_code == 302 and has_client_id and has_redirect_uri

            details = f"Status: {response.status_code}"
            if has_client_id:
                # Extract client_id from URL
                client_id_start = location.find('client_id=') + 10
                client_id_end = location.find('&', client_id_start)
                client_id = location[client_id_start:client_id_end] if client_id_end > 0 else location[client_id_start:]
                details += f", Client ID: {client_id[:20]}..."

            self.log_test("OAuth Login Redirect", passed, details)
            return passed
        except Exception as e:
            self.log_test("OAuth Login Redirect", False, error=str(e))
            return False

    def test_api_without_auth(self):
        """Test 3: API endpoints require authentication"""
        endpoints = [
            "/api/employees",
            "/api/timeoff",
            "/api/audit/logs"
        ]

        all_protected = True
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                # Should return 401 or redirect to login
                is_protected = response.status_code in [401, 302]
                if not is_protected:
                    all_protected = False
                    self.log_test(
                        f"API Protection - {endpoint}",
                        False,
                        f"Status: {response.status_code} (expected 401 or 302)"
                    )
            except Exception as e:
                self.log_test(f"API Protection - {endpoint}", False, error=str(e))
                all_protected = False

        if all_protected:
            self.log_test("API Authentication Required", True, "All endpoints properly protected")
        return all_protected

    def test_static_assets(self):
        """Test 4: Static assets load correctly"""
        try:
            # Get the index page to find asset paths
            response = self.session.get(f"{BASE_URL}/")
            html = response.text

            # Extract asset paths
            assets = []
            if '/assets/' in html:
                import re
                asset_pattern = r'(?:src|href)="(/assets/[^"]+)"'
                assets = re.findall(asset_pattern, html)

            if not assets:
                self.log_test("Static Assets", False, "No assets found in HTML")
                return False

            all_loaded = True
            for asset in assets[:5]:  # Test first 5 assets
                asset_url = f"{BASE_URL}{asset}"
                asset_response = self.session.get(asset_url)
                if asset_response.status_code != 200:
                    all_loaded = False
                    self.log_test(
                        f"Asset Load - {asset}",
                        False,
                        f"Status: {asset_response.status_code}"
                    )

            if all_loaded:
                self.log_test("Static Assets", True, f"All {len(assets[:5])} tested assets loaded successfully")
            return all_loaded
        except Exception as e:
            self.log_test("Static Assets", False, error=str(e))
            return False

    def test_spa_routing(self):
        """Test 5: SPA routing works (non-existent routes return index.html)"""
        try:
            response = self.session.get(f"{BASE_URL}/some-fake-route-12345")
            # Should return 200 with index.html (SPA fallback)
            passed = response.status_code == 200 and "Employee Portal" in response.text
            self.log_test(
                "SPA Routing Fallback",
                passed,
                f"Status: {response.status_code}, Returns index.html: {passed}"
            )
            return passed
        except Exception as e:
            self.log_test("SPA Routing Fallback", False, error=str(e))
            return False

    def test_oauth_scopes(self):
        """Test 6: OAuth request includes all required scopes"""
        try:
            response = self.session.get(f"{BASE_URL}/auth/login", allow_redirects=False)
            location = response.headers.get('Location', '')

            required_scopes = [
                'userinfo.email',
                'userinfo.profile',
                'admin.directory.user',
                'calendar',
                'gmail.send',
                'chat.messages'
            ]

            missing_scopes = [scope for scope in required_scopes if scope not in location]
            passed = len(missing_scopes) == 0

            if passed:
                self.log_test("OAuth Scopes", True, f"All {len(required_scopes)} required scopes present")
            else:
                self.log_test(
                    "OAuth Scopes",
                    False,
                    f"Missing scopes: {', '.join(missing_scopes)}"
                )
            return passed
        except Exception as e:
            self.log_test("OAuth Scopes", False, error=str(e))
            return False

    def test_security_headers(self):
        """Test 7: Security headers are present"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            headers = response.headers

            # Check for important security headers
            security_checks = {
                "X-Content-Type-Options": headers.get("X-Content-Type-Options") == "nosniff",
                "X-Frame-Options": "X-Frame-Options" in headers,
                "Strict-Transport-Security": "Strict-Transport-Security" in headers,
            }

            passed_checks = sum(security_checks.values())
            total_checks = len(security_checks)

            details = f"{passed_checks}/{total_checks} security headers present"
            for header, present in security_checks.items():
                if not present:
                    details += f"\n  Missing: {header}"

            self.log_test(
                "Security Headers",
                passed_checks >= 2,  # At least 2 out of 3
                details
            )
            return passed_checks >= 2
        except Exception as e:
            self.log_test("Security Headers", False, error=str(e))
            return False

    def test_response_times(self):
        """Test 8: Response times are acceptable"""
        try:
            endpoints = [
                "/",
                "/auth/login",
            ]

            all_fast = True
            times = []
            for endpoint in endpoints:
                response = self.session.get(f"{BASE_URL}{endpoint}", allow_redirects=False)
                response_time = response.elapsed.total_seconds()
                times.append(response_time)

                if response_time > 3.0:  # 3 second threshold
                    all_fast = False

            avg_time = sum(times) / len(times)
            details = f"Average: {avg_time:.2f}s, Max: {max(times):.2f}s"

            self.log_test(
                "Response Times",
                all_fast,
                details
            )
            return all_fast
        except Exception as e:
            self.log_test("Response Times", False, error=str(e))
            return False

    def run_all_tests(self):
        """Run all tests and generate report"""
        print("=" * 60)
        print("EMPLOYEE PORTAL - PRODUCTION QA TEST SUITE")
        print(f"Testing: {BASE_URL}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()

        # Run tests
        self.test_site_accessibility()
        self.test_oauth_redirect()
        self.test_oauth_scopes()
        self.test_api_without_auth()
        self.test_static_assets()
        self.test_spa_routing()
        self.test_security_headers()
        self.test_response_times()

        # Generate summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print()

        # Save detailed report
        report_file = f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'test_suite': 'Employee Portal Production QA',
                'base_url': BASE_URL,
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': total - passed,
                    'pass_rate': pass_rate
                },
                'results': self.test_results
            }, f, indent=2)

        print(f"Detailed report saved to: {report_file}")
        print()

        return pass_rate >= 80  # 80% pass rate threshold

if __name__ == "__main__":
    tester = ProductionTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
