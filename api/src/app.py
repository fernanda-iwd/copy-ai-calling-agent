from flask import Flask, request
import json
import os
import requests
import json

app = Flask(__name__)


@app.route("/webhook/call-received", methods=["POST"])
def save_call_data():
    webhook_data = request.get_json()
    print("Webhook data for call_id=" + webhook_data["call_id"])
    print(json.dumps(webhook_data))
    return "Webhook data received"

# send call using pathway id
@app.route("/calls/send", methods=["POST"])
def book_apt():

    phone_number = request.args.get("phoneNumber", type=str)
    pathway_id = (
        request.args.get("pathwayId", type=str)
        or "c2e8ce15-655d-4530-8659-d1e1c5d6bd4c"
    )

    input_data = request.get_json()

    url = "https://api.bland.ai/v1/calls"
    authorization = os.environ["BLAND_API_KEY"]

    data = {
        "phone_number": phone_number,
        "from": None,
        "task": "",
        "language": "en",
        "voice": "nat",
        "voice_settings": {},
        "pathway_id": pathway_id,
        "local_dialing": False,
        "max_duration": 12,
        "answered_by_enabled": False,
        "wait_for_greeting": True,
        "record": False,
        "amd": False,
        "interruption_threshold": 100,
        "voicemail_message": None,
        "temperature": None,
        "transfer_phone_number": None,
        "transfer_list": {},
        "metadata": {},
        "pronunciation_guide": [],
        "start_time": None,
        "request_data": input_data,
        "dynamic_data": [],
        "webhook": os.environ["LOCAL_URL"] + "/webhook/call-received",
        "calendly": {},
        "analysis_schema": {
            "is_appointment_booked": "boolean",
            "appointment_time": "YYYY-MM-DD HH:MM:SS",
        },
    }

    headers = {"Content-Type": "application/json", "Authorization": authorization}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    print("Response:")
    print(response.text)

    return response.text

# send call using prompt
@app.route("/calls/call-send", methods=["POST"])
def book_apt_v2():

    phone_number = request.args.get("phoneNumber", type=str)
    input_data = request.get_json()

    default_prompt = """
       You do not need to mention this but for context, you are an AI assistant that will try to book an appointment with a car repair shop. 

        At the start of the call, ask if this number corresponds to {{supplierShopName}}. If it doesn't you can apologize and terminate the call.

        Otherwise, say you are calling on behalf of a fleet company named {{companyName}}.

        Say that you're looking to book an appointment for {{serviceName}} for a {{vehicleYear}} {{vehicleMake}} {{vehicleModel}}. If there is a {{vehicleCustomization}}, mention that too. Ask if the user can service this vehicle. If they can't, then terminate the call politely.

        If they can, ask if they could schedule an appointment on {{firstTimeRange}} or {{secondTimeRange}}

        If they don't have availability during those times then politely terminate the call. If they do have availability during those times, make sure the user gives you a specific time slot (such as 4:00PM ) within the range.

        If you were able to successfully book an appointment then mention the driver's name {{driverFullName}} and their phone number {{driverPhoneNumber}}. Ask the user if they would like you to repeat or spell out that information, and do not ask if it's correct. Once the user is good, thank them and terminate the call.

        If asked about the vehicle color or vehicle plate at any point in the conversation, respond with {{vehicleColor}} and {{vehiclePlate}} correspondingly.

    """

    prompt = input_data.get("prompt", default_prompt)
    if input_data.get("prompt"):
        del input_data["prompt"]

    data = {
        "phone_number": phone_number,
        "from": None,
        "task": prompt,
        "model": "enhanced",
        "language": "en",
        "voice": "nat",
        "voice_settings": {},
        "pathway_id": None,
        "local_dialing": False,
        "max_duration": 12,
        "answered_by_enabled": False,
        "wait_for_greeting": True,
        "record": False,
        "amd": False,
        "interruption_threshold": 100,
        "voicemail_message": None,
        "temperature": None,
        "transfer_phone_number": None,
        "transfer_list": {},
        "metadata": {},
        "pronunciation_guide": [],
        "start_time": None,
        "request_data": input_data,
        "tools": [],
        "dynamic_data": [],
        "analysis_schema": {
            "is_appointment_booked": "boolean",
            "appointment_time": "YYYY-MM-DD HH:MM:SS",
        },
        "webhook": os.environ["LOCAL_URL"] + "/webhook/call-received",
        "calendly": {},
    }

    headers = {
        "Authorization": os.environ["BLAND_API_KEY"],
    }

    url = "https://api.bland.ai/v1/calls"
    response = requests.post(url, json=data, headers=headers)

    print("Response:")
    print(response.text)

    return response.text


if __name__ == "__main__":
    app.run(host="0.0.0.0")
