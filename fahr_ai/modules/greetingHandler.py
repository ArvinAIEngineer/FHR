import asyncio
from typing import Dict
from AIAgents.base_agent import BaseAgent, GraphState

class GreetingHandler(BaseAgent):
    
    def __init__(self, bot_name:str = "FAHR Virtual Assistant"):
        self.BOT_NAME = bot_name

    async def run(self, channel_type:str, user_name:str, language:str = "en") -> GraphState:
        """Handle greeting scenarios following exact JSON format"""  
        if language == "en":
            greeting_msg_private = f"Hi {user_name}! 👋 I am {self.BOT_NAME}, your virtual assistant in Federal Authority for Government Human Resources (FAHR)! How can I assist you today?"
            greeting_msg_public = f"Hi! I am {self.BOT_NAME}, your virtual assistant in Federal Authority for Government Human Resources (FAHR). In order to enhance this conversation, how do you want me to call you?"
        else:
            greeting_msg_private = f"مرحبًا {user_name}! 👋 أنا {self.BOT_NAME}، مساعدك الافتراضي في الهيئة الاتحادية للموارد البشرية الحكومية (FAHR)! كيف يمكنني مساعدتك اليوم؟"
            greeting_msg_public = f"مرحبًا! 👋 أنا {self.BOT_NAME}، مساعدك الافتراضي في الهيئة الاتحادية للموارد البشرية الحكومية (FAHR)! كيف يمكنني مساعدتك اليوم؟"
        
        if channel_type=="PRIVATE" and user_name:
            return greeting_msg_private
        else:
            return greeting_msg_public