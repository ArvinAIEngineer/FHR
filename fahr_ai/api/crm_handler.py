#crm_handler.py
##Author: Vaibhav Sagar
##Date: 2025-05-30
##Notes - This module handles CRM ticket retrieval and comment fetching using asynchronous HTTP requests.

import httpx
from utils.logger import get_logger
from typing import List, Dict
import asyncio
import os

os.environ['NO_PROXY'] = '10.254.115.17'

class CRMTicketHandler:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = get_logger()

    async def fetch_tickets(self, runtime_config: dict) -> List[Dict]:
        """
        Fetch tickets from the Bayanati CRM API or fallback to an alternate CRM API.
        This method retrieves tickets for the user specified in the runtime_config.
        returns a list of tickets or an empty list if no tickets are found.
        """
        userInfo = runtime_config["configurable"]["userInfo"]
        person_id = userInfo.get("personId", "")
        full_name = userInfo.get("employeeName", "Unknown User")
        user_role = runtime_config["configurable"].get("user_role", "default_role")
        channel_type = runtime_config["configurable"].get("channel_type", "txt")
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                headers = {
                    "Host": "10.254.115.17:8090",
                    "User-Agent": "curl/7.81.0",
                    "Accept": "*/*"
                }
                bayanati_url = f"{self.base_url}/Bayanati/bayanati-api/api/CrmAPI/CaseRetrival?userName={person_id}"
                self.logger.info(f"Fetching tickets for user: {person_id} from {bayanati_url}")
                response = await client.get(bayanati_url, headers=headers)
                response.raise_for_status()
                result = response.json()
                self.logger.debug(f"Response from Bayanati CRM API: {result}")
                if result.get("isSuccess"):
                    return result
                else:
                    self.logger.warning("Bayanati API responded but isSuccess is False.")
        except Exception as e:
            self.logger.error(f"Bayanati API failed: {str(e)}")

        # Fallback to alternate CRM API
        self.logger.info("Attempting fallback CRM API after Bayanati failure...")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Step 1: Get auth token
                auth_url = f"{self.base_url}/api/Auth/GenerateToken"
                auth_payload = {
                    "personId": 123456,  # Placeholder, replace with actual personId
                    "username": full_name, # Placeholder, replace with actual username
                    "role": [user_role],
                    "channel": channel_type,
                }
                self.logger.info(f"Requesting auth token with payload: {auth_payload}")
                auth_response = await client.post(auth_url, json=auth_payload)
                auth_response.raise_for_status()
                auth_data = auth_response.json()
                self.logger.info(f"Auth response: {auth_data}")
                token = auth_data["data"]["accessToken"]

                # Step 2: Hit GetCRMTickets with token
                user_email = userInfo.get("emailAddress", "")
                tickets_url = f"{self.base_url}/api/CRM/GetCRMTickets?customerEmail={user_email}"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                ticket_response = await client.get(tickets_url, headers=headers)
                ticket_response.raise_for_status()
                tickets = ticket_response.json()
                self.logger.info(f"Fetched {len(tickets.get('CaseDetails', []))} tickets using fallback API")
                return tickets
        except Exception as e:
            self.logger.error(f"Fallback API failed: {str(e)}")
            return {}

    async def fetch_comments(self, case_number: str) -> List[Dict]:
        url = f"{self.base_url}/Bayanati/bayanati-api/api/CrmAPI/CrmRetrieveComment"
        self.logger.info(f"Fetching comments for case number: {case_number}")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                headers = {
                    "Host": "10.254.115.17:8090",
                    "User-Agent": "curl/7.81.0",
                    "Accept": "*/*"
                }
                payload = {"caseNumber": case_number}
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                self.logger.info(f"Fetched {len(result.get('Data', []))} comments for case number {case_number}")
                self.logger.debug(f"Response from CRM API for comments: {result}")
                return result.get("Data", []) if result.get("isSuccess") else []
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP status error: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            self.logger.error(f"Request error: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return []

    async def get_ticket_data(self, runtime_config: dict) -> Dict[str, Dict]:
        """
        Fetch and process all ticket data for the given user, using all CRM_Case_Number
        values from the CaseDetails list in the response.
        """
        tickets = await self.fetch_tickets(runtime_config)
        
        case_details = tickets.get("CaseDetails", [])

        if not case_details:
            self.logger.warning("No case details found in the fetched tickets.")
            return {}
        
        self.logger.info(f"Fetched {len(case_details)} tickets for user {runtime_config['configurable']['userInfo'].get('employeeName', 'unknown')}")

        ticket_data = {
            "open": [],
            "closed": []
        }
        raw_ticket_map = {}

        async def process_ticket(ticket):
            case_id = ticket.get("CRM_Case_Number")
            if not case_id:
                self.logger.warning(f"Ticket missing CRM_Case_Number: {ticket}")
                return
            
            raw_ticket_map[case_id] = ticket
            # Fetch comments from API
            comments_api = await self.fetch_comments(case_id)
            # Get other fields from ticket
            status = ticket.get("StatusID", "").lower()
            resolution_remarks = ticket.get("ResolutionRemarks", "")
            crm_service_name = ticket.get("CrmServiceName")
            crm_group_name = ticket.get("CrmGroupName")
            request_details = ticket.get("RequestDetails")
            resolution = ticket.get("Resolution", "")

            # Prepare comments as a list (ResolutionRemarks + API comments)
            if status == "assigned":
                # Open ticket: use comments (ResolutionRemarks + API comments)
                comments_list = []
                if resolution_remarks:
                    comments_list.append(resolution_remarks)
                if comments_api:
                    comments_list.extend(comments_api)
            else:
                # Closed ticket: use resolution as the only comment
                comments_list = [resolution] if resolution else []

            ticket_dict = {
                "id": case_id,
                "crm_service_name": crm_service_name,
                "crm_group_name": crm_group_name,
                "request_details": request_details,
                "comments": comments_list,
                "resolution": resolution
                }

            # Classify as open or closed
            if status == "assigned":
                ticket_data["open"].append(ticket_dict)
            else:
                ticket_data["closed"].append(ticket_dict)

        # Process in batches of 5 per second
        batch_size = 5
        for i in range(0, len(case_details), batch_size):
            batch = case_details[i:i+batch_size]
            await asyncio.gather(*(process_ticket(ticket) for ticket in batch))
            if i + batch_size < len(tickets):
                await asyncio.sleep(1)  # Wait 1 second between batches

        self.logger.info(f"Processed {len(ticket_data)} tickets for user {username}")
        self.logger.debug(f"Ticket data: {ticket_data}")
        return ticket_data