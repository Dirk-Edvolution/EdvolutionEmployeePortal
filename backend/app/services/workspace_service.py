"""
Google Workspace Admin SDK integration service
"""
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from backend.config.settings import WORKSPACE_DOMAIN


class WorkspaceService:
    """Service for interacting with Google Workspace Admin SDK"""

    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.admin_service = build('admin', 'directory_v1', credentials=credentials)

    def list_all_users(self) -> List[Dict[str, Any]]:
        """Fetch all users from Google Workspace"""
        users = []
        page_token = None

        while True:
            try:
                results = self.admin_service.users().list(
                    customer='my_customer',
                    maxResults=500,
                    orderBy='email',
                    pageToken=page_token
                ).execute()

                users.extend(results.get('users', []))
                page_token = results.get('nextPageToken')

                if not page_token:
                    break

            except Exception as e:
                print(f"Error fetching users: {e}")
                break

        return users

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a specific user by email"""
        try:
            user = self.admin_service.users().get(userKey=email).execute()
            return user
        except Exception as e:
            print(f"Error fetching user {email}: {e}")
            return None

    def update_user(self, email: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user information in Google Workspace"""
        try:
            updated_user = self.admin_service.users().update(
                userKey=email,
                body=user_data
            ).execute()
            return updated_user
        except Exception as e:
            print(f"Error updating user {email}: {e}")
            return None

    def update_user_custom_fields(
        self,
        email: str,
        manager_email: Optional[str] = None,
        job_title: Optional[str] = None,
        department: Optional[str] = None,
        location: Optional[str] = None
    ) -> bool:
        """Update user custom fields that sync back to Workspace"""
        try:
            update_body = {}

            # Update relations (manager)
            if manager_email:
                update_body['relations'] = [{
                    'value': manager_email,
                    'type': 'manager',
                    'customType': ''
                }]

            # Update organizations (job title, department)
            if job_title or department:
                org_info = {}
                if job_title:
                    org_info['title'] = job_title
                if department:
                    org_info['department'] = department
                org_info['primary'] = True

                update_body['organizations'] = [org_info]

            # Update locations
            if location:
                update_body['locations'] = [{
                    'type': 'desk',
                    'area': location
                }]

            if update_body:
                self.update_user(email, update_body)
                return True

            return False

        except Exception as e:
            print(f"Error updating custom fields for {email}: {e}")
            return False

    def get_user_manager(self, email: str) -> Optional[str]:
        """Get user's manager email from Workspace"""
        user = self.get_user(email)
        if not user:
            return None

        relations = user.get('relations', [])
        for relation in relations:
            if relation.get('type') == 'manager':
                return relation.get('value')

        return None

    def move_user_to_ou(self, email: str, ou_path: str) -> bool:
        """
        Move a user to a different Organizational Unit

        Args:
            email: User's email address
            ou_path: Target OU path (e.g., '/Employees', '/External', '/Others')

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure OU path starts with /
            if not ou_path.startswith('/'):
                ou_path = '/' + ou_path

            update_body = {
                'orgUnitPath': ou_path
            }

            updated_user = self.admin_service.users().update(
                userKey=email,
                body=update_body
            ).execute()

            print(f"Successfully moved {email} to {ou_path}")
            return True

        except Exception as e:
            print(f"Error moving user {email} to {ou_path}: {e}")
            return False

    def sync_all_users_to_portal(self, firestore_service, filter_ou: str = None) -> int:
        """
        Sync all Google Workspace users to the employee portal

        Args:
            firestore_service: Firestore service instance
            filter_ou: Optional OU path to filter users (e.g., '/Employees')

        Returns:
            Number of users synced
        """
        users = self.list_all_users()
        synced_count = 0

        for user in users:
            try:
                # Skip suspended users
                if user.get('suspended', False):
                    continue

                # Filter by OU if specified
                if filter_ou:
                    user_ou = user.get('orgUnitPath', '/')
                    if not user_ou.startswith(filter_ou):
                        continue

                firestore_service.sync_employee_from_workspace(user)
                synced_count += 1
            except Exception as e:
                print(f"Error syncing user {user.get('primaryEmail')}: {e}")

        return synced_count
