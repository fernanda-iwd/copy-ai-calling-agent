import requests
import json
import os
import time
from openai import AzureOpenAI
from datetime import datetime


class AIAgentHelper:

    def __init__(self, *args, **kwargs):
        super(AIAgentHelper, self).__init__(*args, **kwargs)
        self.INBOUND_PHONE_NUMBER = os.environ["INBOUND_PHONE_NUMBER"]
        self.CALL_DETAILS_URL = "https://api.bland.ai/v1/calls/"
        self.INBOUND_CALL_URL = (
            "https://api.bland.ai/v1/inbound/" + self.INBOUND_PHONE_NUMBER
        )
        self.CALL_URL = (
            os.environ["LOCAL_URL"]
            + "/calls/call-send?phoneNumber="
            + self.INBOUND_PHONE_NUMBER
        )
        self.AZURE_OPENAI_CLIENT = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version="2024-02-01",
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        )
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(script_dir, "prompts")
        self.PROMPTS = {}
        for prompt_file in os.listdir(prompt_path):
            with open(os.path.join(prompt_path, prompt_file), "r") as f:
                agent_name = prompt_file.split(".")[0]
                self.PROMPTS[agent_name] = f.read()
        self.SHORT_POLLING_INTERVAL = 10

    def is_time_in_range(self, range_str, booked_time_str):
        """
        Check if the booked time is within the given time range
        """
        datetime_format = "%Y-%m-%d %H:%M:%S"
        date_range, time_range = range_str.split(" ", 1)
        start_time_str, end_time_str = time_range.split(" - ")
        start_datetime_str = f"{date_range} {start_time_str}"
        end_datetime_str = f"{date_range} {end_time_str}"
        start_datetime = datetime.strptime(start_datetime_str, datetime_format)
        end_datetime = datetime.strptime(end_datetime_str, datetime_format)
        booked_time = datetime.strptime(booked_time_str, datetime_format)
        return start_datetime <= booked_time <= end_datetime

    def setup_inbound_agent(
        self,
        shop_name,
        services,
        vehicles_requirements,
        time_ranges,
        additional_instructions="",
    ):
        """
        Setup the inbound agent acting as the repair shop using Bland API
        """
        endpoint = self.INBOUND_CALL_URL
        headers = {
            "Content-Type": "application/json",
            "authorization": os.environ["BLAND_API_KEY"],
        }
        services = "\n".join([f"- {service}" for service in services])
        vehicles_requirements = "\n".join(
            [f"- {vehicle}" for vehicle in vehicles_requirements]
        )
        time_ranges = "\n".join([f"- {time_range}" for time_range in time_ranges])

        prompt_template = self.PROMPTS["INBOUND_AGENT"].format(
            shop_name=shop_name,
            services=services,
            vehicles_requirements=vehicles_requirements,
            time_ranges=time_ranges,
            additional_instructions=additional_instructions,
        )

        payload = json.dumps(
            {
                "prompt": prompt_template,
                "analysis_schema": {},
            }
        )
        requests.request("POST", endpoint, headers=headers, data=payload)

    def trigger_call(self, payload):
        """
        Trigger a call using Bland API to from the AI Agent to the repair shop inbound agent
        """
        endpoint = self.CALL_URL
        headers = {"Content-Type": "application/json"}
        response = requests.request(
            "POST", endpoint, headers=headers, data=json.dumps(payload)
        )
        if response.status_code != 200:
            raise requests.exceptions.RequestException(
                f"Failed to trigger call: {response.text}"
            )
        call_id = response.json()["call_id"]
        return call_id

    def write_logs(self, test_id, logs):
        """
        Write the call logs to a file based on the test_id
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logs_path = os.path.join(script_dir, "logs", test_id + ".json")
        with open(logs_path, "w") as f:
            f.write(json.dumps(logs))

    def get_call_details(self, call_id, test_id):
        """
        Get the call details from Bland API given the call_id
        """
        time.sleep(self.SHORT_POLLING_INTERVAL)
        endpoint = self.CALL_DETAILS_URL + call_id
        payload = {}
        headers = {"authorization": os.environ["BLAND_API_KEY"]}
        response = requests.request("GET", endpoint, headers=headers, data=payload)
        data = response.json()
        print("Call in progress...")
        while data["status"] != "completed" or not data["analysis"]:
            time.sleep(self.SHORT_POLLING_INTERVAL)
            response = requests.request("GET", endpoint, headers=headers, data=payload)
            data = response.json()
        self.write_logs(test_id, data)
        print("Call completed\n")
        return data

    def assert_analysis(self, data, expected_booking_success, time_range, fail_msg):
        """
        Use Bland's analysis to determine if the test should pass
        """
        analysis = data["analysis"]
        if not analysis:
            return False, "No analysis found"
        if not expected_booking_success:
            if analysis["is_appointment_booked"]:
                return False, fail_msg
            return True, ""
        if not analysis["is_appointment_booked"]:
            return False, fail_msg
        booked_time = analysis["appointment_time"]
        if time_range and not self.is_time_in_range(time_range, booked_time):
            return False, fail_msg
        return True, ""

    def assert_llm(self, data, expected_behavior):
        """
        Analyze the call details using OpenAI and determine if the test should pass
        """
        # Extract the necessary information from the call details
        driver_full_name = data["variables"]["driverFullName"]
        driver_phone_number = data["variables"]["driverPhoneNumber"]
        vehicle_color = data["variables"]["vehicleColor"]
        vehicle_year = data["variables"]["vehicleYear"]
        vehicle_make = data["variables"]["vehicleMake"]
        vehicle_model = data["variables"]["vehicleModel"]
        vehicle_plate = data["variables"]["vehiclePlate"]
        vehicle_customization = data["variables"].get("vehicleCustomization", "")
        driver_vehicle_info = (
            f"{vehicle_color} {vehicle_year} {vehicle_make} {vehicle_model} "
            f"with license plate {vehicle_plate}. {vehicle_customization}"
        )
        service_type = data["variables"]["serviceName"]
        driver_first_time_window = data["variables"]["firstTimeRange"]
        driver_second_time_window = data["variables"]["secondTimeRange"]
        transcript = data["concatenated_transcript"]

        # Fill in the template with the extracted information
        data = f"""
        - Driver's full name: {driver_full_name}
        - Driver's phone number:{driver_phone_number}
        - Driver's vehicle information: {driver_vehicle_info}
        - Type of service: {service_type}
        - Driver's first preferred time window: {driver_first_time_window}
        - Driver's second preferred time window: {driver_second_time_window}
        - Transcript of the call: {transcript}
        - Expected behavior: {expected_behavior}
        """

        prompt_template = self.PROMPTS["TESTING_AGENT"]

        # Use OpenAI to analyze the call details and determine if the test should pass
        try:
            response = self.AZURE_OPENAI_CLIENT.chat.completions.create(
                model=os.environ["AZURE_DEPLOYMENT_NAME"],
                messages=[
                    {
                        "role": "system",
                        "content": prompt_template,
                    },
                    {"role": "user", "content": data},
                ],
            )
        except Exception as e:
            return False, str(e)

        # Extract the response from OpenAI and check if the test passed
        result = response.choices[0].message.content.strip()
        if result != "True":
            explanation = result.split("\n")[1]
            return False, explanation
        return True, ""

    def log_results(self, test_id, call_id, result, msg):
        """
        Log the results of test_id to results.json
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        results_path = os.path.join(script_dir, "logs", "results.json")
        if not os.path.exists(results_path):
            with open(results_path, "w") as f:
                f.write(json.dumps({}))
        with open(results_path, "r") as f:
            results = json.load(f)
        results[test_id] = {"call_id": call_id, "passed": result, "explanation": msg}
        with open(results_path, "w") as f:
            f.write(json.dumps(results))
