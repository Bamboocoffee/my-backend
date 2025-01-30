# 3rd Party Packages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Custom Agents & Utilities
from app.utilities.LangSmithTraceAPI import LangSmithRestAPI
from app.agents.LangChainAgent import LangChainAgent

# Services
from app.services.oura_service import OuraServiceAPI

# Tools
import os


# TODO
# 1) Create bespoke tool for Google Sheets
# 2) Edit tool to accept all sorts of inputs from text
# 3) Connect to Oura account and save to google sheets
# 4) Build agent to tell me what to do every morning


def test_agent_function(content="Can you log that I'm 92kgs today"):
    # result = fetch_oura_personal_info()
    agent_object = LangChainAgent(memory=False) # sets up the orchestration for the agent
    agent_executor = agent_object.create_agent() # creates the agent 
    config = {"configurable": {"thread_id": agent_object.get_thread_id}}

    for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=content)]}, config
        ):
        print(chunk)

    # print(result)
    # Investiagte : https://python.langchain.com/api_reference/core/output_parsers/langchain_core.output_parsers.string.StrOutputParser.html
    return True