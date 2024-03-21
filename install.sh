#!/bin/bash

# Global configurations and paths
SRCDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/ && pwd)"
KLIPPER_PATH="${HOME}/klipper"
SYSTEMDDIR="/etc/systemd/system"
MOONRAKER_ASVC="${HOME}/printer_data/moonraker.asvc"
MOONRAKER_CONFIG="${HOME}/printer_data/config/moonraker.conf"
MA3D_SERVICE="${SYSTEMDDIR}/ma3d.service"
MA3D_DIR="${HOME}/MA3D"
CURRENT_USER=${USER}

# Ensure the script exits on any error
set -e

# Verify if the script is run as the root user
# This function checks if the current user is not root and exits with an error if it is.
# Running as root is not recommended for this script due to potential security risks and permissions issues.
verify_not_root() {
    if [ "$EUID" -eq 0 ]; then
        echo "Error: This script should not be run as root. Please run as a regular user." >&2
        exit 1
    else
        echo "User verification passed."
    fi
}

add_updater()
{
    echo -n "Checking for existing update manager in moonraker.conf... "
    # Define pattern to search for the existing updater section
    start_pattern='^\[update_manager[a-z ]* ma3d\]'
    end_pattern='^\['
    # Use awk to remove the existing section if it exists
    # This awk script checks lines between start_pattern and the next section start (end_pattern)
    # and excludes them from the output.
    awk -v start="$start_pattern" -v end="$end_pattern" '
        $0 ~ start {flag=1; next}
        $0 ~ end && flag {flag=0}
        !flag
    ' "$MOONRAKER_CONFIG" > temp_moonraker.conf && mv temp_moonraker.conf "$MOONRAKER_CONFIG"

    echo -n "Adding or updating update manager in moonraker.conf... "
    # Append the new updater configuration from update_manager.txt
    cat "./config/update_manager.txt" >> "$MOONRAKER_CONFIG"
    echo "[OK]"

    # Add service access to Moonraker, if not already present
    echo -n "Checking and updating moonraker.asvc... "
    if ! grep -q "ma3d" "$MOONRAKER_ASVC"; then
        echo "ma3d" >> "$MOONRAKER_ASVC"
        echo "[UPDATED]"
    else
        echo "[SKIPPED]"
    fi
}

create_service()
{
    # Define the path to the predefined service file
    PREDEFINED_SERVICE_FILE="./config/ma3d.service"

    echo -n "Copying $PREDEFINED_SERVICE_FILE to $MA3D_SERVICE... "
    # Copy the predefined service file to the systemd directory
    sudo cp "$PREDEFINED_SERVICE_FILE" "$MA3D_SERVICE"
    echo "[OK]"

    echo -n "Enabling and starting $MA3D_SERVICE... "
    # Enable and start the service
    sudo systemctl enable ma3d.service
    sudo systemctl start ma3d.service
    echo "[OK]"
}

restart_moonraker()
{
    echo -n "Restarting Moonraker... "
    sudo systemctl restart moonraker
    echo "[OK]"
}

# Run steps
verify_not_root
add_updater
create_service
restart_moonraker
