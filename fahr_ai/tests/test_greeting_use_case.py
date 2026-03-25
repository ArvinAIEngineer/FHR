import unittest
import asyncio
from unittest.mock import AsyncMock
from fahr_ai.modules.greetingHandler import GreetingHandler

class TestGreetingHandler(unittest.TestCase):
    def setUp(self):
        self.user_service = AsyncMock()
        self.handler = GreetingHandler(self.user_service)
    
    def run_async(self, coro):
        """Helper to run async tests"""
        return asyncio.get_event_loop().run_until_complete(coro)
    
    def test_private_channel_authenticated_with_name(self):
        """Test private channel with authenticated user having name"""
        self.user_service.get_profile.return_value = {
            'is_authenticated': True,
            'name': 'Mohamed'
        }
        state = {
            'input': {
                "userId": 123,
                "sessionId": 456,
                "sessionStart": True,
                "channel": "internal_app",
                "personId": 789,
                "inputType": "text",
                "textMessage": "Hi"
            }
        }
        
        result = self.run_async(self.handler.run(state))
        output = result['output']
        
        self.assertEqual(output['status'], 'success')
        self.assertIn("Hi Mohamed! 👋", output['textMessage'])
        self.assertEqual(output['channel'], 'internal_app')
        self.assertEqual(output['personId'], 789)
        self.assertEqual(output['outputType'], 'text')

    def test_public_channel_session_start(self):
        """Test public channel with session start"""
        state = {
            'input': {
                "userId": 111,
                "sessionId": 222,
                "sessionStart": True,
                "channel": "public_website",
                "inputType": "text",
                "textMessage": "Hello"
            }
        }
        
        result = self.run_async(self.handler.run(state))
        output = result['output']
        
        self.assertIn("how do you want me to call you", output['textMessage'])
        self.assertEqual(output['channel'], 'public_website')
        self.assertEqual(output['status'], 'success')

    def test_error_handling(self):
        """Test error scenario when profile service fails"""
        self.user_service.get_profile.side_effect = Exception("API Error")
        state = {
            'input': {
                "userId": 123,
                "sessionId": 456,
                "channel": "internal_app",
                "personId": 789,
                "inputType": "text",
                "textMessage": "Hi"
            }
        }
        
        result = self.run_async(self.handler.run(state))
        output = result['output']
        
        self.assertEqual(output['status'], 'error')
        self.assertIn("technical difficulties", output['textMessage'])
        self.assertEqual(output['personId'], 789)

if __name__ == "__main__":
    unittest.main()