#!/bin/bash

# Ensure the script exits on any error
set -e

install_AWS()
{
    echo -n "Restarting Moonraker... "
    sudo unzip connect_device_package.zip
    sudo chmod +x start.sh
    sudo ./start.sh
}

install_AWS