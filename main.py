from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
import requests
app = FastAPI()

class WebhookData(BaseModel):
    object: str
    entry: list

class hub(BaseModel):
    mode:str
    verify_token:str
    challenge:str

import uvicorn
import sys

import logging


from pymongo import MongoClient
from datetime import datetime

# MongoDB connection details
uri = "mongodb+srv://gaurgoutam:TeqvsnxkbjBqfITC@cluster0.crxdwu1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)


whatsapp_access="EAAUkyJswIjQBO8eLD3Xeh0pdV0RsoQ7CrgZAVaY7mVkHXWRZCRRWHucoo28NkKOKakIExOqpt1kSR1aKEkcgWLeUrYN8VY07yU2WubDv0RPivEWI4W3ZCTmLBSsPiLmOQtoscUkOHqywXXnJcwYL9E5KcSco5M6iiJcOkTzNfDwffYQWEyUmNAmnsj5AgMH6uTrAa0QX4BsY7ZCFLIQO7NC4vvkZD"
# Specify the database and collection
db = client['Palampur']
collection = db['sample_1000']
def check_and_update_serial(serial_no):
    # Find the document by serial number
    doc = collection.find_one({"Serial No": serial_no})
    
    if doc:
        # Check the statuses of RFID and QR code
        status_rfid = doc.get("status_rfid", False)
        status_qr = doc.get("status_qr", False)
        last_updated_time = doc.get("time")  # Retrieve the time field
        
        if status_rfid or status_qr:
            # Both are already True, so it's already scanned
            return f"Already scanned at {last_updated_time}"
        
        else:
            # Update the status_rfid and status_qr if they are False
            update_fields = {}
            
            if not status_rfid:
                update_fields["status_rfid"] = True
            
            if not status_qr:
                update_fields["status_qr"] = True

            if update_fields:
                update_fields["time"] = datetime.utcnow()  # Update the timestamp
                collection.update_one(
                    {"Serial No": serial_no}, 
                    {"$set": update_fields}
                )
                return "Scan status updated successfully"
    else:
        return "Serial number not found"





@app.get("/")
async def read_root():
    return {"message": "Simple WhatsApp Webhook tester. There is no front-end, see main.py for implementation!"}


from fastapi import FastAPI, Request
import logging
import datetime

app = FastAPI()
logging.basicConfig(filename='Whatsapp_response.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Verify token from WhatsApp
verify_token = "token"
def get_changed_field(data):
    return data["entry"][0]["changes"][0]["field"]

def get_mobile(data):
    return data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]

def get_name(data):
    return data["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

def get_message_type(data):
    return data["entry"][0]["changes"][0]["value"]["messages"][0]["type"]

def send_messaging(data):
    status=data["entry"][0]["changes"][0]["value"]["statuses"][0]["status"]
    recipient_id=data["entry"][0]["changes"][0]["value"]["statuses"][0]["recipient_id"]
    timestamp=data["entry"][0]["changes"][0]["value"]["statuses"][0]["timestamp"]
    #timestamp=datetime.datetime.fromtimestamp(int(timestamp))
    return {"status":status,"recipient_id":recipient_id,"timestamp":timestamp}



def recieve_message(data):
    return data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

@app.get("/webhook")
async def subscribe(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == verify_token:
            return int(request.query_params.get('hub.challenge'))
        else:
            return {"status": "error", "message": "Verification failed"}, 403
    else:
        return {"status": "error", "message": "Missing parameters"}, 400
''''''
@app.post("/webhook")
async def callback(request: Request):
    data = await request.json()
    logging.debug(data)
    #return data
    changed_field = get_changed_field(data)
    if "statuses" in data["entry"][0]["changes"][0]["value"]:
        print("Message Sent")
        messaging_info = send_messaging(data)
        print(messaging_info)
        # Log the details
        number = messaging_info["recipient_id"]
        message = "Message Sent"  # You can modify this based on your needs
        status = messaging_info["status"]
        timestamp = messaging_info["timestamp"]
        
    elif changed_field == "messages":
        new_message = get_mobile(data)
        if new_message:
            mobile = get_mobile(data)
            name = get_name(data)
            message_type = get_message_type(data)
            print(f"New Message; sender:{mobile} name:{name} type:{message_type}")
            
            if message_type == "text":
                message = recieve_message(data)
                print("Message: %s", message)
                messages=check_and_update_serial(message)
                send_message(messages, mobile)
    return {"status": "ok"}

def send_message(message, mobile):
    import requests
    import json

    url = 'https://graph.facebook.com/v19.0/315762988298120/messages'
    headers = {
        'Authorization': f'Bearer {whatsapp_access}',
        'Content-Type': 'application/json'
    }
    payload = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': mobile,
        'type': 'text',
        'text': {
            'preview_url': False,
            'body': message
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(response.text)