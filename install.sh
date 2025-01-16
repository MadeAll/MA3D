#!/bin/bash

# Global configurations and paths
SRCDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/ && pwd)"
KLIPPER_PATH="${HOME}/klipper"
SYSTEMDDIR="/etc/systemd/system"
MOONRAKER_ASVC="${HOME}/printer_data/moonraker.asvc"
MOONRAKER_CONFIG="${HOME}/printer_data/config/moonraker.conf"
MA3D_SERVICE="${SYSTEMDDIR}/ma3d.service"
MA3D_DIR="${HOME}/MA3D"
CURRENT_USER=${USER:-"biqu"}  # 기본 값 설정

# Ensure the script exits on any error
set -e

# Verify if the script is run as the root user
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
        echo "\nma3d" >> "$MOONRAKER_ASVC"
        echo "[UPDATED]"
    else
        echo "[SKIPPED]"
    fi
}

install_module() {
    echo -n "Checking and installing Python modules... "

    for module in requests Pillow; do
        if ! python3 -c "import $module" &>/dev/null; then
            echo "Installing $module..."
            pip3 install "$module" || { echo "Failed to install $module"; exit 1; }
        else
            echo "$module is already installed."
        fi
    done

    echo "[OK]"
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

add_config() {
    ORIGINAL_CFG_FILE="./config/MA3D.cfg"
    TARGET_CFG_PATH="/home/biqu/printer_data/config/MA3D.cfg"

    CERT_FILE=$(find "./AWS" -name "*.cert.pem" | head -n 1)
    if [ -z "$CERT_FILE" ]; then
        echo "Error: No AWS certificate file found in ./AWS"
        exit 1
    fi

    ID=$(basename "$CERT_FILE" .cert.pem)
    echo "Using AWS Connection ID: $ID"

    cp "$ORIGINAL_CFG_FILE" "$TARGET_CFG_PATH"
    sed -i "s/^id:.*$/id: ${ID}/" "$TARGET_CFG_PATH"
    echo "[OK] Updated 'id' in MA3D.cfg"


    echo -n "CloudFlare installation... "

    # Cloudflared 설치 여부 확인
    if ! command -v cloudflared &> /dev/null; then
        echo "cloudflared not found. Please install it first."
        exit 1
    fi

    # 터널 존재 여부 확인
    if cloudflared tunnel list | grep -q "printer-$ID"; then
        echo "Tunnel 'printer-$ID' already exists. Skipping creation."
    else
        echo "Creating Cloudflare tunnel with ID 'printer-$ID'..."
        cloudflared tunnel create "printer-$ID"
    fi

    echo "Cloudflare tunnel setup complete."

    # Find the credentials file
    CREDENTIALS_FILE=$(find "/home/biqu/.cloudflared" -type f -name "*.json" | head -n 1)
    if [ -z "$CREDENTIALS_FILE" ]; then
        echo "Error: No .json credentials file found!"
        exit 1
    fi

    CONFIG_FILE="/etc/cloudflared/config.yml"

    # 디렉토리 생성 및 config.yml 작성
    sudo mkdir -p /etc/cloudflared
    # Generate config.yml
    sudo bash -c "cat > $CONFIG_FILE" <<EOL
    tunnel: printer-$ID
    credentials-file: $CREDENTIALS_FILE

    ingress:
    - hostname: printer-$ID.madeall3d.com
      service: http://localhost:80
    - service: http_status:404
EOL

    # Print result
    echo "Config file generated at $CONFIG_FILE"

    sudo cp /home/biqu/.cloudflared/cert.pem /etc/cloudflared/cert.pem

    cloudflared tunnel route dns printer-$ID printer-$ID.madeall3d.com

    # Generate service
    sudo bash -c "cat > /etc/systemd/system/cloudflared.service" <<EOL
    [Unit]
    Description=Cloudflare Tunnel Service
    After=network.target

    [Service]
    Type=simple
    Restart=always
    RestartSec=5s
    ExecStart=/usr/local/bin/cloudflared tunnel run printer-$ID
    WorkingDirectory=/etc/cloudflared
    User=root

    [Install]
    WantedBy=multi-user.target
EOL

    sudo systemctl daemon-reload
    sudo systemctl start cloudflared
    sudo systemctl enable cloudflared
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
install_module
create_service
add_config
restart_moonraker
