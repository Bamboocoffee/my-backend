# 3rd Party Packages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Custom Agents & Utilities
from app.utilities.LangSmithTraceAPI import LangSmithRestAPI
from app.agents.LangChainAgent import LangChainAgent

# Services
from app.services.oura_service import OuraServiceAPI

# Tools
import os
from typing import Dict, List, Optional, Union


# TODO
# - Create bespoke tool for Google Sheets ✅
# - Edit tool to accept all sorts of inputs from text ✅
# - Build basic front-end to interact with tool ✅
# - Edit tool to update sheet with all variables ✅
# - Deploy backend to Heroku 
# - Connect to Oura account and save to google sheets
# - Investigat why the memory is not working
# - Build agent to tell me what to do every morning

  # Process streamed agent responses
def extract_messages(chunk: dict) -> Optional[str]:
        """Extracts AIMessage or ToolMessage content from a chunk."""
        print(chunk)
        for key in ["agent", "tools"]:
            if key in chunk and "messages" in chunk[key]:
                messages = chunk[key]["messages"]
                if messages and isinstance(messages[0], (AIMessage, ToolMessage)):
                    return messages[0].content
        return None

def agent_service(content: str = "No message", user_thread_id: Optional[str] = "") -> Dict[str, Union[List[str], str]]:
    """
    Handles interaction with a LangChain agent, processing a given message 
    and returning AI-generated responses while maintaining conversation context.

    Args:
        content (str, optional): The message to send to the AI agent. Defaults to "No message".
        user_thread_id (str, optional): The thread ID for maintaining conversation history. 
                                        If empty, a new session is created.

    Returns:
        dict: A dictionary containing:
            - "message" (list[str]): AI-generated responses in a structured format.
            - "thread_id" (str): The thread ID associated with the conversation.

    Process:
        1. If `user_thread_id` is provided, initializes `LangChainAgent` with memory.
        2. Creates an agent executor and configures the thread ID.
        3. Streams responses from the agent based on the provided input.
        4. Extracts AI-generated content from `AIMessage` or `ToolMessage` objects.
        5. Returns the extracted responses along with the conversation thread ID.

    Example Usage:
        >>> response = agent_service("Hello!", "1234-5678-uuid")
        >>> print(response)
        {"message": ["Hello! How can I assist you today?"], "thread_id": "1234-5678-uuid"}
    """
    # Initialize the agent, creating a new thread if no thread ID is provided
    try:
        if not user_thread_id:
            agent_object = LangChainAgent() # sets up the orchestration for the agent
        else:
            agent_object = LangChainAgent(memory=True, thread_id=user_thread_id) # sets up the orchestration for the agent
        agent_executor = agent_object.create_agent() # creates the agent 
        config = {"configurable": {"thread_id": ""}}
    except Exception as e:
        print(e)
    
    try:
        streamed_responses = [
            message for chunk in agent_executor.stream({"messages": [HumanMessage(content=content)]}, config)
            if (message := extract_messages(chunk)) is not None
        ]
        return {"message": streamed_responses, "thread_id": ""}
    except Exception as e:
        raise Exception(e)




    # Memory: 
    # 1) Get thread Id from agent 
    # thread_id = agent_object.get_thread_id()

    # 2) Load memory and add chunk
    # past_messages = agent_object.load_memory()
    # conversation_history = [{"messages": past_messages + [HumanMessage(content=content)]}]
    
    # 3) Save & updated messages to memory
    # if agent_object.memory:
    #     agent_object.memory[thread_id] = past_messages + [HumanMessage(content=content)] + streamed_responses