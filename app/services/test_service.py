# 3rd Party Packages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Custom Classes
from app.utilities.LangSmithTraceAPI import LangSmithRestAPI
from app.agents.LangChainAgent import LangChainAgent

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
    # Investiagte : https://python.langchain.com/api_reference/core/output_parsers/langchain_core.output_parsers.string.StrOutputParser.html
    return True