#!/bin/bash

# Ensure the script exits on any error
set -e

restart_moonraker()
{
    echo -n "Restarting Moonraker... "
    sudo cd AWS
    sudo unzip connect_device_package.zip
    sudo chmod +x start.sh
    sudo ./start.sh
}