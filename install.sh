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

install_zrok() {
    echo -n "Checking for zrok-share installation... "

    if ! dpkg-query -W -f='${Status}' zrok-share 2>/dev/null | grep -q "install ok installed"; then
        echo "zrok-share not found, installing..."
        sudo apt install zrok-share
    else
        echo "zrok-share is already installed."
    fi

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

    # Zrok 환경 파일 경로
    ENV_FILE="/opt/openziti/etc/zrok/zrok-share.env"

    ID_LOWER=$(echo "$ID" | tr '[:upper:]' '[:lower:]')  # ID를 소문자로 변환

    # 변경할 변수들
    VARIABLES=(
        "ZROK_ENABLE_TOKEN=\"edAmlRZl7u2k\""
        "ZROK_ENVIRONMENT_NAME=\"$ID_LOWER\""
        "ZROK_UNIQUE_NAME=\"$ID_LOWER\""
    )

    # 각 변수 처리
    for VAR in "${VARIABLES[@]}"; do
        KEY=$(echo "$VAR" | cut -d= -f1)  # 변수 이름 추출
        VALUE=$(echo "$VAR" | cut -d= -f2-)  # 변수 값 추출

        # 변수 이름이 있는 줄 찾기 (주석 포함)
        if grep -q "^#\?\($KEY\)=" "$ENV_FILE"; then
            # 기존 변수 값 변경 (주석이 포함된 경우 주석 제거)
            sudo sed -i "s|^#\?\($KEY\)=.*|\1=$VALUE|" "$ENV_FILE"
        else
            # 변수 추가
            echo "$VAR" | sudo tee -a "$ENV_FILE" > /dev/null
        fi

        # 상태 출력
        echo "Updated $KEY in zrok-share.env"
    done

    # 특수 처리: ZROK_BACKEND_MODE="proxy" 아래의 ZROK_TARGET만 수정
    sudo sed -i '/^ZROK_BACKEND_MODE="proxy"/{
        n
        s|^ZROK_TARGET=.*|ZROK_TARGET="http://127.0.0.1:80"|
    }' "$ENV_FILE"

    echo "Updated ZROK_TARGET under ZROK_BACKEND_MODE=\"proxy\" in zrok-share.env"

    # Moonraker 설정 파일에서 trusted_clients 수정
    MOONRAKER_CFG="/home/biqu/printer_data/config/moonraker.conf"
    echo "Modifying moonraker.cfg: commenting out 127.0.0.0/8 in [authorization]"
    sudo sed -i '/^\s*trusted_clients:/,/^$/ s|^\s*127\.0\.0\.0/8|# 127.0.0.0/8|' "$MOONRAKER_CFG"
    echo "[OK] Updated [authorization] in moonraker.cfg"
    
    # Enable Zrok service
    if ! systemctl is-active --quiet zrok-share.service; then
        sudo systemctl enable --now zrok-share.service
        echo "zrok-share.service is now enabled."
    else
        echo "zrok-share.service is already running."
    fi
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
install_zrok
create_service
add_config
restart_moonraker
