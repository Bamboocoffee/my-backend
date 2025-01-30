# 3rd Party Packages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Custom Agents & Utilities
from app.utilities.LangSmithTraceAPI import LangSmithRestAPI
from app.agents.LangChainAgent import LangChainAgent

# Services
from app.services.oura_service import fetch_oura_personal_info
# Tools
import os

"""
TODO
- Create bespoke tool for Google Sheets
- Connect to Oura account and save to google sheets
- Build agent to tell me what to do every morning
"""
# - Create bespoke tool for Google Sheets
# - Connect to Oura account and save to google sheets


def test_agent_function(content="whats the weather in sf?"):
    result = fetch_oura_personal_info()
    # print(result)
    # Investiagte : https://python.langchain.com/api_reference/core/output_parsers/langchain_core.output_parsers.string.StrOutputParser.html
    return True