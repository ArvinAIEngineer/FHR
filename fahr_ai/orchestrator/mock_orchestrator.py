from typing import Any, Dict


class MockOrchestrator:
    def run(self, userInput: Dict[str, Any]) -> Dict[str, Any]:
        prompt = userInput.get("textMessage", "").lower()

        response_data = {
            "conversationId": userInput.get("conversationId", 0),
            "messageId": 1,
            "widgetType": "text",
            "switchAvatar": "default",
            "type": "text",
            "textData": "",
            "imageData": [],
            "voiceData": [],
            "graphData": {
                "graphType": "bar",  # Required field
                "indexs": [{"name": "Dept A", "color": "#FF0000"}],  # Required field
                "data": [{"value": 10, "title": "Q1", "color": "#00FF00"}]  # Required field
            },
            "fileData": [],
            "videoData": [],
            "tableData": [],
            "navigationData": {
                "targetScreen": "home",  # Required field
                "params": {"itemId": 1, "itemName": "Dashboard"}  # Required field
            },
            "urlData": "",
            "actionButtons": [],
            "faQsData": [],
            "referenceData": []
        }

        if "policy" in prompt:
            response_data["textData"] = "Our HR policy covers leave, attendance, and benefits."
            response_data["fileData"] = [
                {
                    "fileName": "HR_Policy_Guide.pdf",
                    "fileSize": "1.2MB",
                    "file": "base64encodedstring==",
                    "url": "https://example.com/hr_policy.pdf",
                    "fileExt": "pdf"
                }
            ]
        elif "organization chart" in prompt or "structure" in prompt:
            response_data["textData"] = "Here is the latest org chart."
            response_data["imageData"] = [
                {
                    "fileName": "org_chart.png",
                    "fileSize": "500KB",
                    "fileData": "base64imgstring==",
                    "url": "https://example.com/org_chart.png"
                }
            ]
        else:
            response_data["textData"] = f"I received your message: '{userInput.get('textMessage', '')}'"
            response_data["actionButtons"] = [
                {"title": "View Leave Policy", "action": "navigate_leave_policy"},
                {"title": "Contact HR", "action": "contact_hr"}
            ]

        return {
            "success": True,
            "message": "Response generated successfully",
            "statusCode": 200,
            "data": response_data,
            "errors": []
        }
