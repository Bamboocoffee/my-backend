# Import relevant functionality
from uuid import uuid4
from datetime import datetime, timezone
import os
import requests

class LangSmithRestAPI():

    def __init__(self, run_id: uuid4, name: str, run_type: str, inputs: dict = None, parent_id=None):
        """
        Initialize the LangSmith trace on the API

        Parameters:
        :param run_id (uuid4): Unique identifier for the run.
        :param name  (str): Name of the run.
        :param run_type (str): Type of the run.
        :param inputs (dict): Inputs for the run.
        :param parent_id (uuid4, optional): Parent run ID if applicable. Defaults to None.

        Example:
            >>>> lang_smith = LangSmithRestAPI(run_id=uuid4(), name="Chat Pipeline", run_type="chain")
            >>>> lang_smith.post_run(inputs={"question": content})
            >>>> lang_smith.patch_run(outputs={"answer": "This is a test"})
        """
        self.run_id = run_id
        self.name = name
        self.run_type = run_type
        self.inputs = inputs
        self.parent_id = parent_id
        self.headers = self._get_api_key()

    def _get_api_key(self):
        """
        Gets the API key associated with access the LangSmit platform
        """
        return {"x-api-key": os.environ["LANGSMITH_API_KEY"]}


    def post_run(self, inputs: dict) -> None:
        """
        Function to post a new run to the API.

        :params inputs (obj) - the inputs to the class
        """
        self.inputs = inputs
        data = {
            "id": self.run_id.hex,
            "name": self.name,
            "run_type": self.run_type,
            "inputs": self.inputs,
            "start_time": datetime.utcnow().isoformat(),
        }
        if self.parent_id:
            data["parent_run_id"] = self.parent_id.hex
        requests.post(
            "https://api.smith.langchain.com/runs", # Update appropriately for self-hosted installations or the EU region
            json=data,
            headers=self.headers
        )

    def patch_run(self, outputs: dict) -> None:
        """Function to patch a run with outputs
        
        :params outputs (dict) - the output of the model
        """
        requests.patch(
            f"https://api.smith.langchain.com/runs/{self.run_id}",
            json={
                "outputs": outputs,
                "end_time": datetime.now(timezone.utc).isoformat(),
            },
            headers=self.headers,
        )