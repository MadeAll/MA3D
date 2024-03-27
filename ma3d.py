#!/usr/bin/env python3

import time
import datetime
import logging
import os

def setup_logging():
    # Log directory path
    log_dir = "./log"
    # Log file path
    log_file_path = os.path.join(log_dir, "service.log")

    # Create log directory if it does not exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure logging
    logging.basicConfig(filename=log_file_path, level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        filemode='w')  # 'w' to overwrite log file on each start

def main():
    # Setup logging
    setup_logging()

    # Infinite loop to simulate a service
    while True:
        # Get current time
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Log current time to the log file
        logging.info(f"MA3D service is running at {current_time}")
        # Wait for 60 seconds
        time.sleep(60)

if __name__ == "__main__":
    main()
