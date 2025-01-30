from flask import Flask, jsonify, request
import requests
import os

app = Flask(__name__)

# Oura API Base URL
OURA_API_BASE_URL = "https://api.ouraring.com"
OUR_API_KEY =os.getenv("OURA_API_TOKEN")

def daily_readiness():

    url = f"{OURA_API_BASE_URL}/v2/usercollection/daily_sleep"
    params={ 
        'start_date': '2025-01-30', 
        'end_date': '2025-01-31',
        'next_token': None
    }
    headers = {
        "Authorization": f"Bearer {OUR_API_KEY}"
    }
    response = requests.get(url, headers=headers, params=params)
    print(response.json()["data"][0]["score"])
    
    if response.status_code == 200:
        print("Getting here")
        return response.json()  # Successfully fetched data
    elif response.status_code == 401:
        return {"error": "Unauthorized. Check your access token."}, 401
    elif response.status_code == 403:
        return {"error": "Forbidden. Insufficient permissions."}, 403
    elif response.status_code == 404:
        return {"error": "Not found. Invalid API endpoint."}, 404
    else:
        return {"error": "Failed to fetch data", "status_code": response.status_code}, response

def daily_sleep():

    url = f"{OURA_API_BASE_URL}/v2/usercollection/sleep"
    params={ 
        'start_date': '2025-01-29', 
        'end_date': '2025-01-30',
        'next_token': None
    }
    headers = {
        "Authorization": f"Bearer {OUR_API_KEY}"
    }
    response = requests.get(url, headers=headers, params=params)

    average_hrv = response.json()["data"][0]["average_hrv"]
    sleep_duration = response.json()["data"][0]["total_sleep_duration"]
    print(average_hrv)
    print((sleep_duration/60)/60)

    if response.status_code == 200:
        print("Getting here")
        return response.json()  # Successfully fetched data
    elif response.status_code == 401:
        return {"error": "Unauthorized. Check your access token."}, 401
    elif response.status_code == 403:
        return {"error": "Forbidden. Insufficient permissions."}, 403
    elif response.status_code == 404:
        return {"error": "Not found. Invalid API endpoint."}, 404
    else:
        return {"error": "Failed to fetch data", "status_code": response.status_code}, response


def fetch_oura_personal_info():
    """
    Fetches personal information from the Oura API.

    Args:
        access_token (str): The OAuth Bearer token.

    Returns:
        dict: The API response in JSON format.
    """



    return daily_readiness()
    # return daily_sleep()




