from flask import Flask, jsonify, request
import requests
import os

class OuraServiceAPI:
    """Handles requests to the Oura API."""
    
    BASE_URL = "https://api.ouraring.com"
    API_KEY = os.getenv("OURA_API_TOKEN")

    def __init__(self):
        if not self.API_KEY:
            raise ValueError("Missing OURA_API_TOKEN. Set it as an environment variable.")

    def _make_request(self, endpoint: str, params: dict = None):
        """
        Makes a request to the Oura API.

        Args:
            endpoint (str): The Oura API endpoint (e.g., "/v2/usercollection/sleep").
            params (dict, optional): Query parameters. Defaults to None.

        Returns:
            dict: API response or an error message.
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self.API_KEY}"}

        response = requests.get(url, headers=headers, params=params)
        return self._handle_response(response)

    def _handle_response(self, response):
        """
        Handles API response errors and extracts data.

        Args:
            response (requests.Response): The API response object.

        Returns:
            dict: Parsed JSON response or an error message.
        """
        if response.status_code == 200:
            return response.json()
        error_messages = {
            401: "Unauthorized. Check your access token.",
            403: "Forbidden. Insufficient permissions.",
            404: "Not found. Invalid API endpoint."
        }
        return {"error": error_messages.get(response.status_code, "API request failed"), "status_code": response.status_code}

    def get_daily_sleep(self, start_date: str, end_date: str) -> dict:
        """
        Fetches daily readiness scores.

        Args:
            start_date (str): The start date (YYYY-MM-DD).
            end_date (str): The end date (YYYY-MM-DD).

        Returns:
            dict: Readiness data.
        """
        params = {"start_date": start_date, "end_date": end_date, "next_token": None}
        data = self._make_request("/v2/usercollection/daily_sleep", params)
        sleep_score = 0
        if "data" in data and data["data"]:
            sleep_score = data["data"][0]["score"]
        return {"sleep_score": sleep_score}

    def get_sleep_details(self, start_date: str, end_date: str) -> dict:
        """
        Fetches daily sleep data.

        Args:
            start_date (str): The start date (YYYY-MM-DD).
            end_date (str): The end date (YYYY-MM-DD).

        Returns:
            dict: Sleep data.
        """
        params = {"start_date": start_date, "end_date": end_date, "next_token": None}
        data = self._make_request("/v2/usercollection/sleep", params)
        largest_hrv = 0
        longest_sleep = 0
        # print(data)
        try:
            if "data" in data and data["data"]:
                for i, entry in enumerate(data["data"]):
                    largest_hrv = max(data["data"][i]["average_hrv"] or 0, largest_hrv) 
                    longest_sleep = max(data["data"][i]["total_sleep_duration"] / 3600 or 0, longest_sleep)
            return {"total_hrv": largest_hrv, "total_sleep_duration": f"{int(longest_sleep)}:{round((longest_sleep % 1) * 60):02d}"}
        except Exception as e:
            raise Exception(e)

    def get_personal_info(self):
        """
        Fetches personal information from the Oura API.

        Returns:
            dict: User personal data.
        """
        return self.get_daily_readiness("2025-01-30", "2025-01-31")