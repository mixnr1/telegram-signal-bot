import config
import langdetect
from langdetect import detect
import requests
import json
from datetime import datetime

# Set up the base URL for the Telegram API with the token from config
baseURL = f"https://api.telegram.org/bot{config.token_API}/getUpdates"

# Endpoint for sending the POST request
post_url = 'http://localhost:8080/v2/send'
registered_number = config.registered_number
recipient_number = config.recipient_number

# Send the GET request to the Telegram API
resp = requests.get(baseURL)

# Parse the JSON response
data = resp.json()

# Function to extract and format message details
def get_message_details(message):
    message_time_unix = message.get('date')
    message_time = datetime.fromtimestamp(message_time_unix).strftime('%Y-%m-%d %H:%M:%S') if message_time_unix else 'unknown'
    message_author = message['from'].get('username', 'Unknown')
    message_text = message.get('text', '')
    message_language = detect(message_text) if message_text else 'unknown'
    
    return {
        "Time": message_time,
        "Author": message_author,
        "Language": message_language,
        "Message": message_text
    }

# Check if the response contains 'result'
if 'result' in data:
    for update in data['result']:
        # Check if the update contains a message
        if 'message' in update:
            message = update['message']
            message_details = get_message_details(message)
            
            # Prepare the message for the POST request
            post_data = {
                "message": f"Time: {message_details['Time']}, Author: {message_details['Author']}, Language: {message_details['Language']}, Message: {message_details['Message']}",
                "number": registered_number,
                "recipients": [recipient_number]
            }
            
            # Encode the payload in UTF-8
            post_data_json = json.dumps(post_data, ensure_ascii=False).encode('utf-8')
            
            # Send the POST request
            post_resp = requests.post(post_url, headers={"Content-Type": "application/json"}, data=post_data_json)
            
            # Print the response from the POST request
            print(post_resp.text)

else:
    print("No messages found.")
