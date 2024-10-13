import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.agents.structured_chat.base import StructuredChatAgent
from langchain.prompts import MessagesPlaceholder
from langchain.schema.messages import SystemMessage
from langchain_community.tools import BaseTool
from langchain.chains.llm import LLMChain
from langchain.schema import AgentAction, AgentFinish
from langchain.memory import ConversationBufferMemory

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText
from typing import Optional, Type

# Configuration
from dotenv import load_dotenv
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Google API configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/calendar']

def get_google_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Product Database (Mock)
PRODUCT_DATABASE = {
    "product_xyz": {
        "name": "Product XYZ",
        "price": 999.99,
        "features": ["Feature 1", "Feature 2", "Feature 3"],
        "availability": True
    }
}

#Tools
class EmailTool(BaseTool):
    name: str = "send_email"
    description: str = "Useful for sending emails to customers"

    def _run(self, email_content: str, recipient: str, subject: str) -> str:
        try:
            creds = get_google_credentials()
            service = build('gmail', 'v1', credentials=creds)
            
            message = MIMEText(email_content)
            message['to'] = recipient
            message['subject'] = subject
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().messages().send(userId='me', body={'raw': raw}).execute()
            
            return f"Email sent successfully to {recipient}"
        except Exception as e:
            return f"Failed to send email: {str(e)}"

class CalendarTool(BaseTool):
    name: str = "schedule_meeting"
    description: str = "Useful for scheduling meetings with customers. Requires date in ISO format (YYYY-MM-DDTHH:MM:SS)"

    def _run(self, customer_email: str, date: str, duration: int = 60) -> str:
        try:
            # Ensure the date is in the correct format
            try:
                meeting_start = datetime.fromisoformat(date)
                meeting_end = meeting_start + timedelta(minutes=duration)
            except ValueError:
                return "Error: Invalid date format. Please use ISO format (YYYY-MM-DDTHH:MM:SS)"

            creds = get_google_credentials()
            service = build('calendar', 'v3', credentials=creds)
            
            event = {
                'summary': 'Sales Meeting',
                'description': 'Sales meeting scheduled by AI Sales Agent',
                'start': {
                    'dateTime': meeting_start.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': meeting_end.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [
                    {'email': customer_email},
                ],
                'reminders': {
                    'useDefault': True
                },
            }
            
            event = service.events().insert(calendarId='primary', 
                                           body=event,
                                           sendUpdates='all').execute()
            
            meeting_link = event.get('htmlLink', 'No link available')
            return f"""Meeting scheduled successfully:
            With: {customer_email}
            Start: {meeting_start.strftime('%Y-%m-%d %H:%M')}
            Duration: {duration} minutes
            Calendar Link: {meeting_link}"""
        except Exception as e:
            return f"Failed to schedule meeting: {str(e)}"

class ProductInfoTool(BaseTool):
    name: str = "get_product_info"
    description: str = "Useful for getting product information"

    def _run(self, product_id: str) -> str:
        product = PRODUCT_DATABASE.get(product_id.lower())
        if product:
            return f"Product: {product['name']}\nPrice: ${product['price']}\nFeatures: {', '.join(product['features'])}\nAvailable: {'Yes' if product['availability'] else 'No'}"
        return f"Product {product_id} not found"

# Agent
class SalesAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.tools = [
            EmailTool(),
            CalendarTool(),
            ProductInfoTool()
        ]
        
        system_message = SystemMessage(
            content="""You are an AI sales agent assistant. Your goal is to help with sales-related tasks using the tools provided to you."""
        )
        
        agent = StructuredChatAgent.from_llm_and_tools(
            llm=self.llm,
            tools=self.tools,
            system_message=system_message,
        )
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    def run(self, task: str) -> str:
        return self.agent_executor.run(task)

if __name__ == "__main__":
    main()