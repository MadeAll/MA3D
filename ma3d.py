#!/usr/bin/env python3

import time
import datetime

def main():
    # Infinite loop to simulate a service
    while True:
        # Get current time
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Log current time to a file
        with open("/tmp/ma3d.log", "a") as log_file:
            log_file.write(f"{current_time} - MA3D service is running...\n")
        # Wait for 60 seconds
        time.sleep(60)

if __name__ == "__main__":
    main()
