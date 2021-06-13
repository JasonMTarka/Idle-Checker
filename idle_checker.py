import os
import sys
import psutil
import pyautogui
import boto3
import logging
from time import sleep


class Idle_Checker:

    def __init__(self, **kwargs) -> None:

        def logger_setup() -> logging.Logger:

            logger = logging.getLogger(__name__)
            logger.setLevel(logging.INFO)

            formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
            file_handler = logging.FileHandler('idle_checker_logs.log')
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)

            if self.debug:
                stream_handler = logging.StreamHandler()
                stream_handler.setFormatter(formatter)
                logger.addHandler(stream_handler)

            return logger

        self.debug = kwargs.get("debug")
        self.logger = logger_setup()
        self.running = True

        self.ELAPSED_TIME = 0  # Rough elapsed time the program has been running
        self.RUNNING_DURATION = 60 * 60 * 4  # Total allowed running length of program - last digit is # of hours
        self.SLEEP_MODE_LENGTH = 600  # 600 seconds = 10 minutes; time during Sleep Mode between resource check

        self.CPU_THRESHOLD = 30  # Maximum for acceptable CPU usage, in %
        self.MEMORY_THRESHOLD = 50  # Maximum for acceptable RAM usage, in %
        self.RESOURCE_CHECKS = 3  # Number of resource checks required to fail or pass to determine heavy usage
        self.RESOURCE_CHECK_INTERVAL = 3  # Number of seconds between resource checks
        self.MAXIMUM_RESOURCE_CHECKS = 10  # Failsafe value in case checks keep rebounding between active and inactive

        self.PRESENCE_WAIT_TIME = 6  # Number of seconds between presence checks
        self.PRESENCE_CHECK_COUNT = 60  # Number of checks for user presence; with wait time of 6 seconds, 10 checks equals 1 minute

        if self.debug:  # Sets some constant values lower for debugging purposes
            self.RUNNING_DURATION = 30
            self.CPU_THRESHOLD = 10
            self.SLEEP_MODE_LENGTH = 5
            self.PRESENCE_WAIT_TIME = 2
            self.PRESENCE_CHECK_COUNT = 5

    def main(self) -> None:

        def sleep_mode() -> None:

            self.logger.info(f"Entering sleep mode... ({self.SLEEP_MODE_LENGTH} seconds)")
            self.ELAPSED_TIME += self.SLEEP_MODE_LENGTH
            sleep(self.SLEEP_MODE_LENGTH)

        while self.running and self.ELAPSED_TIME <= self.RUNNING_DURATION:
            if self.resource_utilization():  # Checks if resources are being heavily utilized
                if self.presence():  # Checks if user is present
                    sleep_mode()
                else:
                    self.send_notification()  # If resources are being utilized and user is not present, AWS SNS sends a notification email and ends the loop
            else:
                sleep_mode()

        self.logger.info("Closing program...")

    def update_resources(self) -> None:

        self.cpu, self.memory = (psutil.cpu_percent(interval=0.6), psutil.virtual_memory().percent)
        self.logger.info(f"CPU usage is at {self.cpu}% and memory usage is at {self.memory}%.")

    def resource_utilization(self) -> bool:

        resource_counter = 0
        total_checks = 0

        while resource_counter < self.RESOURCE_CHECKS and resource_counter > -self.RESOURCE_CHECKS and total_checks < self.MAXIMUM_RESOURCE_CHECKS:

            sleep(self.RESOURCE_CHECK_INTERVAL)
            self.update_resources()

            if self.cpu >= self.CPU_THRESHOLD or self.memory >= self.MEMORY_THRESHOLD:
                self.logger.info(f"Resources are being heavily utilized. (Maximum CPU usage allowed: {self.CPU_THRESHOLD}%, Maximum RAM usage allowed: {self.MEMORY_THRESHOLD}%)")
                resource_counter += 1
                total_checks += 1

            else:
                self.logger.info(f"Resources not being heavily utilized. (Maximum CPU usage allowed: {self.CPU_THRESHOLD}%, Maximum RAM usage allowed: {self.MEMORY_THRESHOLD}%)")
                resource_counter -= 1
                total_checks += 1

        if resource_counter >= self.RESOURCE_CHECKS:  # Heavy resource usage
            self.logger.warning(f"Computer has failed resource checks. (Total number of checks: {total_checks})")
            return True
        elif resource_counter <= -self.RESOURCE_CHECKS:  # Light resource usage
            self.logger.info(f"Computer has passed resource checks. (Total number of checks: {total_checks})")
            return False
        elif total_checks >= self.MAXIMUM_RESOURCE_CHECKS:  # Total number of checks exceeded
            self.logger.warning(f"Computer has reached maximum number of allowed checks. (Total number of checks: {total_checks})")
            return False
        else:  # Other error catcher
            self.logger.error(f"An unknown error has occured in resource checks. (Total number of checks: {total_checks})")
            return False

    def presence(self) -> bool:

        mouse_x, mouse_y = pyautogui.position()

        for _ in range(self.PRESENCE_CHECK_COUNT):
            sleep(self.PRESENCE_WAIT_TIME)
            self.logger.info("Checking for user presence...")
            mouse_new_x, mouse_new_y = pyautogui.position()
            if mouse_new_x != mouse_x or mouse_new_y != mouse_y:
                self.logger.info("Activity detected.")
                return True

        self.logger.info("User does not seem to be present.")
        return False

    def send_notification(self) -> None:

        self.logger.info("Sending notification via AWS SNS...")

        if self.debug is False:
            client = boto3.client(
                "sns",
                aws_access_key_id=os.environ.get("AWS-Python-Access-Key-ID"),
                aws_secret_access_key=os.environ.get("AWS-Python-Secret-Access-Key"),
                region_name=os.environ.get("AWS-Region")
            )

            client.publish(
                TopicArn=os.environ.get("AWS-Python-Idle-Checker-TopicArn"),
                Message=f"Your CPU usage was recorded at {self.cpu}% and your RAM usage was recorded at {self.memory}%.  Did you leave a task running?",
                Subject="Idle Checker Notification",
            )

        self.running = False


def main():

    debug = False
    for cl_arg in sys.argv[1:]:
        if cl_arg == "--debug" or cl_arg == "-d":
            debug = True

    checker = Idle_Checker(debug=debug)
    checker.main()


if __name__ == "__main__":
    main()
