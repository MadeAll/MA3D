#!/bin/bash

SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/ && pwd )"
KLIPPER_PATH="${HOME}/klipper"
SYSTEMDDIR="/etc/systemd/system"
MOONRAKER_CONFIG="${HOME}/printer_data/config/moonraker.conf"
MA3D_SERVICE="${SYSTEMDDIR}/ma3d.service"
MA3D_DIR="${HOME}/MA3D"
MA3D_ENV="${HOME}/ma3d-env" # 가상 환경 경로가 있다면 이를 사용하시오
CURRENT_USER=${USER}

# Force script to exit if an error occurs
set -e

# Step 1: Check for root user
verify_ready()
{
    # check for root user
    if [ "$EUID" -eq 0 ]; then
        echo "This script must not run as root"
        exit -1
    fi
    echo "User Verified..."
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
    # Now append the new updater configuration
    echo "\n[update_manager ma3d]" >> "$MOONRAKER_CONFIG"
    echo "type: git_repo" >> "$MOONRAKER_CONFIG"
    echo "path: $MA3D_DIR" >> "$MOONRAKER_CONFIG"
    echo "primary_branch: main" >> "$MOONRAKER_CONFIG"
    echo "origin: https://oauth2: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@github.com/MadeAll/MA3D.git" >> "$MOONRAKER_CONFIG"
    echo "managed_services: ma3d" >> "$MOONRAKER_CONFIG"
    echo "\n" >> "$MOONRAKER_CONFIG"
    echo "[OK]"

    echo -n "Restarting Moonraker... "
    sudo systemctl restart moonraker
    echo "[OK]"
}

create_service()
{
    echo -n "Creating $MA3D_SERVICE systemd service file... "
    sudo bash -c "cat > $MA3D_SERVICE" <<EOF
[Unit]
Description=MA3D Service for 3D Printer Management
After=network-online.target moonraker.service

[Service]
Type=simple
User=$CURRENT_USER
ExecStart=/usr/bin/python3 $MA3D_DIR/ma3d.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    echo "[OK]"

    echo -n "Enabling and starting $MA3D_SERVICE... "
    sudo systemctl enable ma3d.service
    sudo systemctl start ma3d.service
    echo "[OK]"
}

# Run steps
verify_ready
add_updater
create_service
