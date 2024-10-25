import requests
import sys
import argparse


class ModelRequestObject:
    # get the essential API keys etc.
    # allow for the model to be specified - if not have a default
    # query the model with a questionn - provide a default
    
    def __init__(self, model_name='google/gemma-2-2b-it', api_token="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"):
        """
        Creates the instance of class. You can stipule a new model if required.

        """
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        self.headers = {"Authorization": f"Bearer {api_token}"}

    def query(self, payload):
        """
        We want to call the API to get response from the model

        Parameters:
        payload (str): this is the input text from the user that will be used to query the model

        Return:
        A json (Dict) that contains the response from the model
        
        """
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        return response.json()    

def main(prompt):
    model_instance = ModelRequestObject()
    response = model_instance.query({
        "inputs": prompt,   

    })
    print(response)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run Hugging Face model with prompt input.")
    parser.add_argument("--prompt", type=str, required=True, help="The prompt to generate text from.")
    
    # Parse the arguments
    args = parser.parse_args()
    
    sys.exit(main(args.prompt))