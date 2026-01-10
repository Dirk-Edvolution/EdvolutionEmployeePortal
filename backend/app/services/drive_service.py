"""
Google Drive and Sheets integration service for trip expense tracking
"""
from typing import Optional, Tuple, Dict, Any
from datetime import date
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class DriveService:
    """Service for managing Google Drive folders and Google Sheets for trip expenses"""

    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.drive_service = build('drive', 'v3', credentials=credentials)
        self.sheets_service = build('sheets', 'v4', credentials=credentials)

    def create_trip_expense_folder(
        self,
        destination: str,
        employee_name: str,
        employee_email: str,
        admin_emails: list,
        trip_date: date
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a Google Drive folder for trip expenses
        Returns (folder_id, folder_url) if successful
        """
        try:
            folder_name = f"Trip - {destination} - {employee_name} - {trip_date.isoformat()}"

            # Create folder metadata
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
            }

            # Create the folder
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id, webViewLink'
            ).execute()

            folder_id = folder.get('id')
            folder_url = folder.get('webViewLink')

            # Share folder with employee and admins
            # Employee gets edit access
            self._share_file(folder_id, employee_email, 'writer')

            # Admins get edit access
            for admin_email in admin_emails:
                if admin_email != employee_email:  # Don't share twice
                    self._share_file(folder_id, admin_email, 'writer')

            return folder_id, folder_url

        except Exception as e:
            print(f"Error creating Drive folder: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    def create_receipts_subfolder(self, parent_folder_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a 'Receipts' subfolder inside the trip folder
        Returns (folder_id, folder_url) if successful
        """
        try:
            folder_metadata = {
                'name': 'Receipts',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }

            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id, webViewLink'
            ).execute()

            return folder.get('id'), folder.get('webViewLink')

        except Exception as e:
            print(f"Error creating Receipts subfolder: {e}")
            return None, None

    def create_expense_spreadsheet(
        self,
        folder_id: str,
        destination: str,
        employee_name: str,
        start_date: date,
        end_date: date,
        purpose: str,
        expected_goal: str,
        estimated_budget: float,
        currency: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a Google Sheet for expense tracking
        Returns (spreadsheet_id, spreadsheet_url) if successful
        """
        try:
            # Create spreadsheet
            spreadsheet = {
                'properties': {
                    'title': f'Expense Report - {destination} - {start_date.isoformat()}'
                },
                'sheets': [
                    {
                        'properties': {
                            'title': 'Trip Info',
                            'gridProperties': {
                                'frozenRowCount': 1
                            }
                        }
                    },
                    {
                        'properties': {
                            'title': 'Expenses',
                            'gridProperties': {
                                'frozenRowCount': 1
                            }
                        }
                    }
                ]
            }

            result = self.sheets_service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result.get('spreadsheetId')

            # Move to folder
            self.drive_service.files().update(
                fileId=spreadsheet_id,
                addParents=folder_id,
                fields='id, parents'
            ).execute()

            # Populate Trip Info sheet
            self._populate_trip_info_sheet(
                spreadsheet_id,
                destination,
                employee_name,
                start_date,
                end_date,
                purpose,
                expected_goal,
                estimated_budget,
                currency
            )

            # Populate Expenses sheet
            self._populate_expenses_sheet(spreadsheet_id, currency)

            # Get URL
            file = self.drive_service.files().get(
                fileId=spreadsheet_id,
                fields='webViewLink'
            ).execute()

            return spreadsheet_id, file.get('webViewLink')

        except Exception as e:
            print(f"Error creating expense spreadsheet: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    def _populate_trip_info_sheet(
        self,
        spreadsheet_id: str,
        destination: str,
        employee_name: str,
        start_date: date,
        end_date: date,
        purpose: str,
        expected_goal: str,
        estimated_budget: float,
        currency: str
    ):
        """Populate the Trip Info sheet with trip details"""
        values = [
            ['Field', 'Value'],
            ['Employee', employee_name],
            ['Destination', destination],
            ['Start Date', start_date.isoformat()],
            ['End Date', end_date.isoformat()],
            ['Purpose', purpose],
            ['Expected Goal', expected_goal],
            ['Estimated Budget', f'{estimated_budget} {currency}'],
            ['Currency', currency],
        ]

        body = {
            'values': values
        }

        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Trip Info!A1',
            valueInputOption='RAW',
            body=body
        ).execute()

        # Format header row
        self._format_header_row(spreadsheet_id, 'Trip Info', 0)

    def _populate_expenses_sheet(self, spreadsheet_id: str, currency: str):
        """Populate the Expenses sheet with column headers and formulas"""
        headers = [
            ['Date', 'Concept/Description', 'Amount', 'Currency', 'Receipt Link', 'Status', 'Notes']
        ]

        # Add summary rows at the top
        summary = [
            ['SUMMARY', '', '', '', '', '', ''],
            ['Total Budget', '=SUM(C10:C1000)', currency, '', '', '', ''],
            ['Total Spent', '=SUM(C10:C1000)', currency, '', '', '', ''],
            ['Total Approved', '0', currency, '', '', '', ''],
            ['To Reimburse', '0', currency, '', '', '', ''],
            ['To Deduct', '0', currency, '', '', '', ''],
            ['', '', '', '', '', '', ''],
            ['', '', '', '', '', '', ''],
            headers[0]
        ]

        body = {
            'values': summary
        }

        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Expenses!A1',
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()

        # Format header row (row 9, 0-indexed = 8)
        self._format_header_row(spreadsheet_id, 'Expenses', 8)

    def _format_header_row(self, spreadsheet_id: str, sheet_name: str, row_index: int):
        """Format a header row with bold text and background color"""
        try:
            # Get sheet ID
            spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheet_id = None
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    break

            if sheet_id is None:
                return

            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': row_index,
                        'endRowIndex': row_index + 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.2,
                                'green': 0.6,
                                'blue': 0.86
                            },
                            'textFormat': {
                                'bold': True,
                                'foregroundColor': {
                                    'red': 1.0,
                                    'green': 1.0,
                                    'blue': 1.0
                                }
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            }]

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()

        except Exception as e:
            print(f"Error formatting header row: {e}")

    def _share_file(self, file_id: str, email: str, role: str = 'writer'):
        """Share a file or folder with a user"""
        try:
            permission = {
                'type': 'user',
                'role': role,  # 'reader', 'writer', 'owner'
                'emailAddress': email
            }

            self.drive_service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=True,
                emailMessage=f'A trip expense folder has been shared with you.'
            ).execute()

        except Exception as e:
            print(f"Error sharing file with {email}: {e}")

    def get_folder_files(self, folder_id: str) -> list:
        """Get list of files in a folder"""
        try:
            query = f"'{folder_id}' in parents and trashed = false"
            results = self.drive_service.files().list(
                q=query,
                fields='files(id, name, mimeType, webViewLink, createdTime)'
            ).execute()

            return results.get('files', [])

        except Exception as e:
            print(f"Error getting folder files: {e}")
            return []
