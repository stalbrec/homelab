import requests
from wakeonlan import send_magic_packet
import time
import logging


# Configuration
logging.basicConfig(level=logging.INFO)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class TNUtils:
    def __init__(self, ip, mac, api_key) -> None:
        self.truenas_ip = ip
        self.truenas_mac = mac
        self.api_key = api_key
        self.base_url = f"http://{self.truenas_ip}/api/v2.0"

    def wake(self):
        """Send a Wake-on-LAN magic packet to the TrueNAS system."""
        logging.info("Waking up TrueNAS...")
        send_magic_packet(self.truenas_mac)

    def is_awake(self):
        """Check if TrueNAS is reachable."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"{self.base_url}/system/info", timeout=5, headers=headers
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_running_tasks(self):
        """Check for running tasks on TrueNAS via API."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"{self.base_url}/core/get_jobs?state=RUNNING", headers=headers
            )
            response.raise_for_status()
            tasks = response.json()
            return tasks
        except requests.exceptions.RequestException as e:
            logging.error(f"Error checking tasks: {e}")
            return []

    def shutdown(self):
        """Send a shutdown command to TrueNAS via API."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.post(
                f"{self.base_url}/system/shutdown", headers=headers
            )
            response.raise_for_status()
            logging.info("Shutdown command sent successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending shutdown command: {e}")


def main(ip, mac, api_key, interval: int = 60, threshold: int = 3600):
    truenas = TNUtils(ip, mac, api_key)
    already_awake = truenas.is_awake()
    if already_awake:
        logging.info("TrueNAS is already up.")
    else:
        logging.info("TrueNAS is down. Waking it up...")
        truenas.wake()
        time.sleep(30)

    while not truenas.is_awake():
        logging.info("Waiting for TrueNAS to come online...")
        time.sleep(10)

    logging.info("TrueNAS is online. Monitoring tasks...")

    no_task_time = 0
    while True:
        tasks = truenas.get_running_tasks()
        if tasks:
            logging.info(f"Observing {len(tasks)} running tasks. Resetting idle timer.")
            no_task_time = 0
        else:
            no_task_time += interval
            logging.info(f"No tasks running. Idle time: {no_task_time} seconds.")

            if no_task_time >= threshold:
                logging.info(
                    "No tasks running for threshold time. Shutting down TrueNAS..."
                )
                truenas.shutdown()
                break

        time.sleep(interval)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor TrueNAS tasks and shutdown when idle."
    )
    parser.add_argument("--ip", help="TrueNAS IP address", required=True)
    parser.add_argument("--mac", help="TrueNAS MAC address", required=True)
    parser.add_argument("--api-key", help="TrueNAS API key", required=True)
    parser.add_argument(
        "--interval", help="Check interval in seconds", type=int, default=60
    )
    parser.add_argument(
        "--threshold", help="Idle threshold in seconds", type=int, default=3600
    )
    args = parser.parse_args()
    main(args.ip, args.mac, args.api_key, args.interval, args.threshold)
