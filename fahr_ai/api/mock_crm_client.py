# mock_crm_client.py
from typing import List, Dict

class MockCRMClient:
    def fetch_all_tickets(self, username: str) -> List[Dict]:
        return [
            {
                "CRM_Case_Number": "CAS-12345-ABCD",
                "RequestDetails": "Request about leave policy",
                "RequestDate": "2025-05-20T10:00:00",
                "StatusID": "Assigned",  # Open
                "ResolutionRemarks": ""
            },
            {
                "CRM_Case_Number": "CAS-54321-DCBA",
                "RequestDetails": "Issue with payroll processing",
                "RequestDate": "2025-05-01T09:00:00",
                "StatusID": "Closed",
                "ResolutionRemarks": "Resolved by adjusting payment"
            }
        ]

    def fetch_ticket_comments(self, case_number: str) -> List[Dict]:
        if case_number == "CAS-12345-ABCD":
            return [
                {
                    "Body": "We are reviewing your request.",
                    "CreatedOn": "2025-05-21T08:30:00",
                    "CreatedBy": "Agent A"
                },
                {
                    "Body": "Forwarded to HR department.",
                    "CreatedOn": "2025-05-22T10:00:00",
                    "CreatedBy": "Agent B"
                }
            ]
        return []
