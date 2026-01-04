"""
Unit tests for self-service portal models
"""
from datetime import datetime, date
from backend.app.models.travel_request import TravelRequest, DisbursementType, ApprovalStatus, ExpenseCategory
from backend.app.models.tool_request import ToolRequest, ToolType
from backend.app.models.employee_asset import EmployeeAsset, AssetType, AssetCategory, AssetStatus


class TestTravelRequest:
    """Tests for TravelRequest model"""

    def test_create_travel_request(self):
        """Test creating a travel request"""
        expenses = [
            {
                'category': ExpenseCategory.AIRFARE.value,
                'description': 'Round trip flight',
                'estimated_cost': 500.00
            },
            {
                'category': ExpenseCategory.ACCOMMODATION.value,
                'description': '3 nights hotel',
                'estimated_cost': 450.00
            }
        ]

        travel = TravelRequest(
            employee_email='test@edvolution.io',
            origin='Mexico City',
            destination='San Francisco',
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 5),
            purpose='Client meeting',
            expenses=expenses,
            total_estimated_cost=950.00,
            currency='USD',
            disbursement_type=DisbursementType.ADVANCE,
            manager_email='manager@edvolution.io'
        )

        assert travel.employee_email == 'test@edvolution.io'
        assert travel.origin == 'Mexico City'
        assert travel.destination == 'San Francisco'
        assert travel.duration_days == 5
        assert travel.total_estimated_cost == 950.00
        assert travel.status == ApprovalStatus.PENDING
        print("✅ Test create_travel_request passed")

    def test_travel_to_dict(self):
        """Test converting travel request to dict"""
        travel = TravelRequest(
            employee_email='test@edvolution.io',
            origin='Mexico City',
            destination='San Francisco',
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 5),
            purpose='Client meeting',
            expenses=[],
            total_estimated_cost=500.00,
            currency='USD',
            disbursement_type=DisbursementType.REIMBURSEMENT,
            manager_email='manager@edvolution.io'
        )

        data = travel.to_dict()
        assert data['employee_email'] == 'test@edvolution.io'
        assert data['origin'] == 'Mexico City'
        assert data['disbursement_type'] == 'reimbursement'
        assert data['status'] == 'pending'
        assert 'created_at' in data
        print("✅ Test travel_to_dict passed")

    def test_travel_from_dict(self):
        """Test creating travel request from dict"""
        data = {
            'employee_email': 'test@edvolution.io',
            'origin': 'Mexico City',
            'destination': 'San Francisco',
            'start_date': '2026-02-01',
            'end_date': '2026-02-05',
            'purpose': 'Client meeting',
            'expenses': [],
            'total_estimated_cost': 500.00,
            'currency': 'USD',
            'disbursement_type': 'advance',
            'status': 'pending',
            'manager_email': 'manager@edvolution.io',
            'created_at': datetime.utcnow().isoformat()
        }

        travel = TravelRequest.from_dict('test-id', data)
        assert travel.request_id == 'test-id'
        assert travel.employee_email == 'test@edvolution.io'
        assert travel.disbursement_type == DisbursementType.ADVANCE
        print("✅ Test travel_from_dict passed")

    def test_travel_approval_workflow(self):
        """Test travel request approval workflow"""
        travel = TravelRequest(
            employee_email='employee@edvolution.io',
            origin='Mexico City',
            destination='San Francisco',
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 5),
            purpose='Client meeting',
            expenses=[],
            total_estimated_cost=500.00,
            currency='USD',
            disbursement_type=DisbursementType.ADVANCE,
            manager_email='manager@edvolution.io'
        )

        # Initial status
        assert travel.status == ApprovalStatus.PENDING

        # Manager approval
        assert travel.can_approve_manager('manager@edvolution.io', 'manager@edvolution.io')
        travel.approve_by_manager('manager@edvolution.io')
        assert travel.status == ApprovalStatus.MANAGER_APPROVED
        assert travel.manager_approved_by == 'manager@edvolution.io'

        # Admin approval
        admin_users = ['admin@edvolution.io']
        assert travel.can_approve_admin('admin@edvolution.io', admin_users)
        travel.approve_by_admin('admin@edvolution.io')
        assert travel.status == ApprovalStatus.APPROVED
        assert travel.admin_approved_by == 'admin@edvolution.io'

        print("✅ Test travel_approval_workflow passed")

    def test_travel_rejection(self):
        """Test travel request rejection"""
        travel = TravelRequest(
            employee_email='employee@edvolution.io',
            origin='Mexico City',
            destination='San Francisco',
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 5),
            purpose='Client meeting',
            expenses=[],
            total_estimated_cost=500.00,
            currency='USD',
            disbursement_type=DisbursementType.ADVANCE,
            manager_email='manager@edvolution.io'
        )

        travel.reject('manager@edvolution.io', 'Budget constraints')
        assert travel.status == ApprovalStatus.REJECTED
        assert travel.rejected_by == 'manager@edvolution.io'
        assert travel.rejection_reason == 'Budget constraints'
        print("✅ Test travel_rejection passed")


class TestToolRequest:
    """Tests for ToolRequest model"""

    def test_create_tool_request(self):
        """Test creating a tool request"""
        tool = ToolRequest(
            employee_email='test@edvolution.io',
            tool_type=ToolType.LAPTOP,
            justification='Current laptop is 5 years old',
            manager_email='manager@edvolution.io'
        )

        assert tool.employee_email == 'test@edvolution.io'
        assert tool.tool_type == ToolType.LAPTOP
        assert tool.display_name == 'Laptop'
        assert tool.status == ApprovalStatus.PENDING
        print("✅ Test create_tool_request passed")

    def test_custom_tool_request(self):
        """Test creating a custom tool request"""
        tool = ToolRequest(
            employee_email='test@edvolution.io',
            tool_type=ToolType.CUSTOM,
            justification='Need for specific project',
            custom_description='Standing desk converter',
            custom_price=299.99,
            custom_link='https://example.com/product',
            manager_email='manager@edvolution.io'
        )

        assert tool.tool_type == ToolType.CUSTOM
        assert tool.custom_description == 'Standing desk converter'
        assert tool.custom_price == 299.99
        assert tool.display_name == 'Standing desk converter'
        print("✅ Test custom_tool_request passed")

    def test_tool_approval_workflow(self):
        """Test tool request approval workflow"""
        tool = ToolRequest(
            employee_email='employee@edvolution.io',
            tool_type=ToolType.MONITOR,
            justification='Need second monitor for productivity',
            manager_email='manager@edvolution.io'
        )

        # Manager approval
        tool.approve_by_manager('manager@edvolution.io')
        assert tool.status == ApprovalStatus.MANAGER_APPROVED

        # Admin approval
        tool.approve_by_admin('admin@edvolution.io')
        assert tool.status == ApprovalStatus.APPROVED

        print("✅ Test tool_approval_workflow passed")


class TestEmployeeAsset:
    """Tests for EmployeeAsset model"""

    def test_create_employee_asset(self):
        """Test creating an employee asset"""
        asset = EmployeeAsset(
            employee_email='test@edvolution.io',
            asset_type=AssetType.HARDWARE,
            category=AssetCategory.LAPTOP,
            description='MacBook Pro 16" 2024',
            assigned_date=date(2024, 6, 15),
            assigned_by='hr@edvolution.io',
            serial_number='C02XK0ECMD6M',
            cost=2500.00,
            currency='USD'
        )

        assert asset.employee_email == 'test@edvolution.io'
        assert asset.asset_type == AssetType.HARDWARE
        assert asset.category == AssetCategory.LAPTOP
        assert asset.is_hardware == True
        assert asset.is_subscription == False
        assert asset.is_active == True
        assert asset.status == AssetStatus.ACTIVE
        print("✅ Test create_employee_asset passed")

    def test_subscription_asset(self):
        """Test creating a subscription asset"""
        asset = EmployeeAsset(
            employee_email='test@edvolution.io',
            asset_type=AssetType.SUBSCRIPTION,
            category=AssetCategory.WORKSPACE,
            description='Google Workspace Business',
            assigned_date=date(2024, 1, 1),
            assigned_by='hr@edvolution.io',
            cost=12.00,
            currency='USD'
        )

        assert asset.is_subscription == True
        assert asset.is_hardware == False
        print("✅ Test subscription_asset passed")

    def test_asset_return(self):
        """Test returning an asset"""
        asset = EmployeeAsset(
            employee_email='test@edvolution.io',
            asset_type=AssetType.HARDWARE,
            category=AssetCategory.LAPTOP,
            description='MacBook Pro',
            assigned_date=date(2024, 6, 15),
            assigned_by='hr@edvolution.io'
        )

        assert asset.is_active == True

        asset.return_asset(date(2026, 1, 4))

        assert asset.status == AssetStatus.RETURNED
        assert asset.return_date == date(2026, 1, 4)
        assert asset.is_active == False
        print("✅ Test asset_return passed")

    def test_asset_to_dict(self):
        """Test converting asset to dict"""
        asset = EmployeeAsset(
            employee_email='test@edvolution.io',
            asset_type=AssetType.HARDWARE,
            category=AssetCategory.MONITOR,
            description='Dell 27" Monitor',
            assigned_date=date(2024, 6, 15),
            assigned_by='hr@edvolution.io',
            cost=350.00
        )

        data = asset.to_dict()
        assert data['employee_email'] == 'test@edvolution.io'
        assert data['asset_type'] == 'hardware'
        assert data['category'] == 'monitor'
        assert data['cost'] == 350.00
        assert 'created_at' in data
        print("✅ Test asset_to_dict passed")


def run_all_tests():
    """Run all tests"""
    print("\n🧪 Running Self-Service Portal Model Tests\n")
    print("=" * 60)

    # Travel Request Tests
    print("\n📋 Testing TravelRequest Model:")
    print("-" * 60)
    test_travel = TestTravelRequest()
    test_travel.test_create_travel_request()
    test_travel.test_travel_to_dict()
    test_travel.test_travel_from_dict()
    test_travel.test_travel_approval_workflow()
    test_travel.test_travel_rejection()

    # Tool Request Tests
    print("\n🛠️  Testing ToolRequest Model:")
    print("-" * 60)
    test_tool = TestToolRequest()
    test_tool.test_create_tool_request()
    test_tool.test_custom_tool_request()
    test_tool.test_tool_approval_workflow()

    # Employee Asset Tests
    print("\n📦 Testing EmployeeAsset Model:")
    print("-" * 60)
    test_asset = TestEmployeeAsset()
    test_asset.test_create_employee_asset()
    test_asset.test_subscription_asset()
    test_asset.test_asset_return()
    test_asset.test_asset_to_dict()

    print("\n" + "=" * 60)
    print("✅ All tests passed successfully!")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    run_all_tests()
