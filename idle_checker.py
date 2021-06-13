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
            file_handler = logging.FileHandler('idle_checker.log')
            file_handler.setFormatter(formatter)

            if self.debug:
                stream_handler = logging.StreamHandler()
                stream_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(stream_handler)

            return logger

        def debug_mode() -> None:
            # Sets constants to lower levels for debugging purposes

            self.RUNNING_DURATION = 30
            self.CPU_THRESHOLD = 10
            self.SLEEP_MODE_LENGTH = 10
            self.PRESENCE_WAIT_TIME = 2
            self.PRESENCE_CHECK_COUNT = 3

        self.debug = kwargs.get("debug")
        self.logger = logger_setup()

        self.ELAPSED_TIME = 0  # Rough elapsed time the program has been running
        self.RUNNING_DURATION = 60 * 60 * 4  # Total running length of program - last digit is # of hours
        self.CPU_THRESHOLD = 30  # Maximum for acceptable CPU usage, in %
        self.MEMORY_THRESHOLD = 50  # Maximum for acceptable RAM usage, in %
        self.SLEEP_MODE_LENGTH = 600  # 600 seconds = 10 minutes; time during Sleep Mode between resource check
        self.PRESENCE_WAIT_TIME = 6  # Time between checks when checking user's presence
        self.PRESENCE_CHECK_COUNT = 60  # Number of checks for user presence; with wait time of 6 seconds, 10 checks equals 1 minute
        self.running = True

        if self.debug:
            debug_mode()

    def main(self) -> None:

        def sleep_mode() -> None:

            self.logger.info(f"Entering sleep mode... ({self.SLEEP_MODE_LENGTH} seconds)")
            self.ELAPSED_TIME += self.SLEEP_MODE_LENGTH
            sleep(self.SLEEP_MODE_LENGTH)

        while self.running and self.ELAPSED_TIME <= self.RUNNING_DURATION:
            self.update_resources()
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

        if self.cpu >= self.CPU_THRESHOLD or self.memory >= self.MEMORY_THRESHOLD:
            self.logger.info(f"Resources are being heavily utilized. (Maximum CPU usage allowed: {self.CPU_THRESHOLD}%, Maximum RAM usage allowed: {self.MEMORY_THRESHOLD}%)")
            return True
        else:
            self.logger.info(f"Resources not being heavily utilized. (Maximum CPU usage allowed: {self.CPU_THRESHOLD}%, Maximum RAM usage allowed: {self.MEMORY_THRESHOLD}%)")
            return False

    def presence(self) -> bool:

        mouse_x, mouse_y = pyautogui.position()
        sleep(self.PRESENCE_WAIT_TIME)

        for _ in range(self.PRESENCE_CHECK_COUNT):
            self.logger.info("Checking for user presence...")
            mouse_new_x, mouse_new_y = pyautogui.position()
            if mouse_new_x != mouse_x or mouse_new_y != mouse_y:
                self.logger.info("User is present.")
                return True
            sleep(self.PRESENCE_WAIT_TIME)

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
