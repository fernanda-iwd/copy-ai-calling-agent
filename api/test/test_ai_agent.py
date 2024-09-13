import unittest
import os
import json
from helper import AIAgentHelper


class TestAIAgent(unittest.TestCase):

    def setUp(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(script_dir, "data.json")
        with open(data_path, "r", encoding="UTF-8") as f:
            self.PAYLOAD = json.load(f)
        self.helper = AIAgentHelper()

    def run_test(
        self,
        test_id,
        shop_name,
        services,
        vehicles_requirements,
        available_time_ranges,
        payload,
        expected_booking_success,
        fail_msg,
        expected_behavior,
        valid_time_range="",
        additional_instructions="",
    ):
        print(f"\n\nRunning {test_id}\n\n")
        print("Setting up inbound agent...")
        self.helper.setup_inbound_agent(
            shop_name=shop_name,
            services=services,
            vehicles_requirements=vehicles_requirements,
            time_ranges=available_time_ranges,
            additional_instructions=additional_instructions,
        )
        print("Inbound agent setup completed\n")
        print("Triggering call...")
        call_id = self.helper.trigger_call(payload=payload)
        data = self.helper.get_call_details(call_id=call_id, test_id=test_id)
        print("Call details received\n")

        print("Asserting call details...")

        result, msg = self.helper.assert_analysis(
            data=data,
            expected_booking_success=expected_booking_success,
            time_range=valid_time_range,
            fail_msg=fail_msg,
        )

        if not result:
            self.helper.log_results(
                test_id=test_id, call_id=call_id, result=result, msg=msg
            )
            self.fail(msg)

        result, msg = self.helper.assert_llm(
            data=data, expected_behavior=expected_behavior
        )

        print("Assertions completed\n")

        self.helper.log_results(
            test_id=test_id, call_id=call_id, result=result, msg=msg
        )
        self.assertTrue(result, msg)

    def test_tc001(self):
        """
        TC001: Agent cannot book appointment because the wrong shop is called
        """
        self.run_test(
            test_id="TC001",
            shop_name="Midas",
            services=["any service"],
            vehicles_requirements=["any vehicle"],
            available_time_ranges=["any date/time available"],
            payload=self.PAYLOAD,
            fail_msg="Appointment was booked even though an incorrect shop was called",
            expected_booking_success=False,
            expected_behavior="""
                The appointment should NOT be booked because an incorrect shop was called.
                Agent should have politely informed the shop that they dialed the wrong number
                and ended the call.
            """,
        )

    def test_tc002(self):
        """
        TC002: Agent cannot book appointment because the shop cannot service this vehicle
        """
        self.run_test(
            test_id="TC002",
            shop_name="Firestone",
            services=["any service"],
            vehicles_requirements=[
                "must NOT weigh more than 1,500 kilograms",
                "must NOT be a Tesla",
            ],
            available_time_ranges=["any date/time available"],
            payload=self.PAYLOAD,
            fail_msg="Appointment was booked even though the shop does not service this specific vehicle",
            expected_booking_success=False,
            expected_behavior="""
                The appointment should NOT be booked because the shop does not
                service the specific vehicle requested as it weighs more than
                1500 kilograms.
            """,
        )

    def test_tc003(self):
        """
        TC003: No vehicle customization is provided; appointment is booked as normal
        """
        payload = self.PAYLOAD.copy()
        payload.pop("vehicleCustomization", None)
        self.run_test(
            test_id="TC003",
            shop_name="Firestone",
            services=["brake servicing", "oil change"],
            vehicles_requirements=["any vehicle"],
            available_time_ranges=["any date/time available"],
            payload=payload,
            fail_msg="Appointment was not booked at all",
            expected_booking_success=True,
            expected_behavior="""
                The appointment should be booked as normal even if no vehicle customization
                is provided.
            """,
        )

    def test_tc004(self):
        """
        TC004: Shop has availability and gives a specific time slot within first time range
        """
        self.run_test(
            test_id="TC004",
            shop_name="Firestone",
            services=["brake servicing", "oil change"],
            vehicles_requirements=[
                "you can service any vehicle without any restrictions"
            ],
            available_time_ranges=[
                "2024-08-19 9:00:00 - 17:00:00",
            ],
            payload=self.PAYLOAD,
            fail_msg="Appointment was not booked in the driver's first preferred time range",
            expected_booking_success=True,
            expected_behavior="""
                The appointment should ONLY be booked in the driver's first preferred time range.
            """,
            valid_time_range=self.PAYLOAD["firstTimeRange"],
            additional_instructions="""
                When the driver suggests a preferred time range, confirm if the range is available or not.
                Then provide a specific time that is within the available time ranges that also works for the driver.
            """,
        )

    def test_tc005(self):
        """
        TC005: Shop has availability and gives a specific time slot within second time range
        """
        self.run_test(
            test_id="TC005",
            shop_name="Firestone",
            services=["brake servicing", "oil change"],
            vehicles_requirements=[
                "you can service any vehicle without any restrictions"
            ],
            available_time_ranges=[
                "2024-08-20 9:00:00 - 17:00:00",
            ],
            payload=self.PAYLOAD,
            fail_msg="Appointment was not booked in the driver's second preferred time range",
            expected_booking_success=True,
            expected_behavior="""
                The appointment should ONLY be booked in the driver's second preferred time range.
            """,
            valid_time_range=self.PAYLOAD["secondTimeRange"],
            additional_instructions="""
                When the driver suggests a preferred time range, confirm if the range is available or not given the times given above.
                Then provide a specific time that is within the available time ranges that also works for the driver.
            """,
        )

    def test_tc006(self):
        """
        TC006: Shop does not have availability within the first or second time range and does not suggest any alternatives
        """
        self.run_test(
            test_id="TC006",
            shop_name="Firestone",
            services=["brake servicing", "oil change"],
            vehicles_requirements=[
                "you can service any vehicle without any restrictions"
            ],
            available_time_ranges=[
                "2024-08-24 9:00:00 - 17:00:00",
            ],
            payload=self.PAYLOAD,
            fail_msg="Appointment was booked even though neither time ranges were available",
            expected_booking_success=False,
            expected_behavior="""
                The appointment should NOT be booked because neither time ranges were available.
            """,
            additional_instructions="""
                When the driver suggests a preferred time range, confirm if the range is available or not.
                If the range is not available, do not provide any alternatives. Wait for the driver to suggest a time
                and if the suggested time is not available, inform the driver that you are unable to help them and end the call.
            """,
        )

    def test_tc007(self):
        """
        TC007: Shop does not have availability within the first or second time range and suggests an alternative
        """
        self.run_test(
            test_id="TC007",
            shop_name="Firestone",
            services=["brake servicing", "oil change"],
            vehicles_requirements=[
                "you can service any vehicle without any restrictions"
            ],
            available_time_ranges=[
                "2024-08-24 9:00:00 - 17:00:00",
            ],
            payload=self.PAYLOAD,
            fail_msg="Appointment was booked even though neither time ranges were available",
            expected_booking_success=False,
            expected_behavior="""
                The appointment should NOT be booked because neither time ranges were available.
            """,
            additional_instructions="""
                When the driver suggests a preferred time range, confirm if the range is available or not.
                If the range is not available, offer a specific time that is within the available time ranges in the order they were provided.
                If this time slot does not work for the driver, inform them that you are unable to help them
                and end the call.
            """,
        )


if __name__ == "__main__":
    unittest.main()
