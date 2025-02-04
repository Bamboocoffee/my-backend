from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Custom Tools
from app.agents.tools.GoogleSheetsTool import CustomGoogleSheetsTool

# Tools
from uuid import uuid4
from typing import Optional


class LangChainAgent():
    """
    A general AI agent that integrates with a language model, tools, and memory capabilities.

    Attributes:
        model (ChatOpenAI): The language model used by the agent.
        tools (list): The list of tools available for the agent.
        memory (bool): Indicates whether the agent has memory enabled.
        _thread_id (str or None): Internal thread ID for tracking execution.

    Example:
        >>>> agent_object = LangChainAgent() # sets up the orchestration for the agent
        >>>> agent_executor = agent_object.create_agent() # creates the agent 
        >>>> config = {"configurable": {"thread_id": agent_object.get_thread_id}}
    """

    # _thread_id = None

    def __init__(self, model= ChatOpenAI(), tools: list = ["search", "spreadsheet"], memory: bool=True, thread_id: Optional[str] = None):
        """
        Initializes the GeneralAgent with a specified model, tools, and memory settings.

        Args:
            model (ChatOpenAI, optional): The language model instance. Defaults to a new instance of ChatOpenAI.
            tools (list of str, optional): A list of tool names that the agent can use. Defaults to ["search"].
            memory (bool, optional): Whether the agent should have memory enabled. Defaults to True.
        """
        self.model = model
        self.tools = self._get_tools(tools)
        self.memory = MemorySaver() if memory else None
        self._thread_id = thread_id if thread_id else (["1234"] if memory else None)
        # self.memory = self._overlord(shouldPossessMemory=memory)


    def _get_tools(self, tools: list) -> list:
        """
        =Private Class=

        This is a sample method to add required tools / expose to the agent. The user should pass the tool function to expose to the model

        :params tools [str] - a list of the tools in string

        Returns
        -------
        List of tools

        """
        tools_to_use = []
        for tool in tools: # For more tools simple add more functionality
            if tool == 'search':
                tools_to_use.append(TavilySearchResults(max_results=2))
            elif tool == 'spreadsheet':
                tools_to_use.append(CustomGoogleSheetsTool(
                    service_account_file='google_service_account.json', 
                    spreadsheet_id='1Duy4XcvZzmk69HV4l0WPfoSO9UNbbtbX6IMMUOaZDQ4',
                    scopes=["https://www.googleapis.com/auth/spreadsheets"],
                    sheet_range="Daily Tracker!A1:Z11637",
                    )
                )
        return tools_to_use

    def _overlord(self, shouldPossessMemory: bool) -> object:
        """
        If the user wishes we create a memory for the conversation via a class instanciation
        We also create a unique thread ID for the conversation

        :params shouldPossessMemory - should the model remember
        """
        return MemorySaver() if shouldPossessMemory else None
        
    
    def get_thread_id(self) -> Optional[str]:
        """
        Method that allows programs to access the thread id
        """
        return self._thread_id

    def load_memory(self):
        """
        Loads stored messages from memory.
        Returns:
            List[HumanMessage | AIMessage | ToolMessage]: Retrieved messages.
        """
        try:
            if self.memory and self._thread_id:
                stored_messages = self.memory.get(self._thread_id)
                # ✅ Fix: Ensure messages are properly loaded
                if stored_messages and isinstance(stored_messages, str):  
                    try:
                        stored_messages = eval(stored_messages)  # Convert from string to list
                    except Exception as e:
                        print(f"Error parsing memory for {self._thread_id}: {e}")
                        stored_messages = []
                return stored_messages if isinstance(stored_messages, list) else []
        except Exception as e:
            print(e)
        return []
    
    def create_agent(self):
        """
        Instanciates the agent for workload
        """
        return create_react_agent(self.model, self.tools, checkpointer=self.memory)