#!/usr/bin/env python3
import requests
from wakeonlan import send_magic_packet
import time
import logging
import argparse


def setup_logging(log_path):
    if log_path:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            filename=log_path,
        )
    else:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


class TNUtils:
    def __init__(self, ip, mac, api_key) -> None:
        self.truenas_ip = ip
        self.truenas_mac = mac
        self.api_key = api_key
        self.base_url = f"http://{self.truenas_ip}/api/v2.0"

    def __repr__(self) -> str:
        return f"TNUtils(IP={self.truenas_ip}, MAC={self.truenas_mac}, api_key=*****)"

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


def main():

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
        "--threshold",
        help="Idle threshold in seconds.",
        type=int,
        default=3600,
        # this should be above whatever the delta between the start of the script and the first check is
        # since there will always be a couple of tasks after the system booted.
        # TODO: make this a bit more dynamic, i.e. filter out tasks that are older than the script start or of a certain type
    )
    parser.add_argument("--debug", help="Enable debug logging", action="store_true")
    parser.add_argument("--log", help="Log file path")
    args = parser.parse_args()

    setup_logging(args.log)

    truenas = TNUtils(args.ip, args.mac, args.api_key)
    logging.info(f"Starting TrueNAS monitor with {truenas}")
    logging.info(f"Check interval: {args.interval} seconds")
    logging.info(f"Idle threshold: {args.threshold} seconds")

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
            no_task_time += args.interval
            logging.info(f"No tasks running. Idle time: {no_task_time} seconds.")

            if no_task_time >= args.threshold:
                logging.info(
                    "No tasks running for threshold time. Shutting down TrueNAS..."
                )
                truenas.shutdown()
                break

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
