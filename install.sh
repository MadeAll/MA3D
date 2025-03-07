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
# AWS 인증서에서 추출한 ID를 전역 변수로 선언
ID=""
# 임시 파일 경로
TEMP_CONFIG="$(mktemp)"

# 스크립트 종료 시 임시 파일 정리
cleanup() {
    rm -f "$TEMP_CONFIG"
}

# 오류 발생 시 정리 및 종료
error_exit() {
    echo "Error: $1" >&2
    cleanup
    exit 1
}

# 스크립트 종료 시 cleanup 함수 호출
trap cleanup EXIT

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

# 필요한 디렉토리 확인
check_directories() {
    echo -n "Checking required directories... "
    
    # printer_data 디렉토리 확인
    if [ ! -d "${HOME}/printer_data" ]; then
        error_exit "printer_data directory not found in ${HOME}"
    fi
    
    # config 디렉토리 확인
    if [ ! -d "${HOME}/printer_data/config" ]; then
        mkdir -p "${HOME}/printer_data/config" || error_exit "Failed to create config directory"
    fi
    
    # AWS 디렉토리 확인
    if [ ! -d "./AWS" ]; then
        error_exit "AWS directory not found in current directory"
    fi
    
    # config 디렉토리 확인
    if [ ! -d "./config" ]; then
        error_exit "config directory not found in current directory"
    fi
    
    echo "[OK]"
}

add_updater() {
    echo -n "Checking for existing update manager in moonraker.conf... "
    
    # moonraker.conf 파일 존재 확인
    if [ ! -f "$MOONRAKER_CONFIG" ]; then
        error_exit "moonraker.conf not found at $MOONRAKER_CONFIG"
    fi
    
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
    ' "$MOONRAKER_CONFIG" > "$TEMP_CONFIG" || error_exit "Failed to process moonraker.conf"
    
    # 임시 파일을 원본으로 이동
    mv "$TEMP_CONFIG" "$MOONRAKER_CONFIG" || error_exit "Failed to update moonraker.conf"

    echo -n "Adding or updating update manager in moonraker.conf... "
    # update_manager.txt 파일 존재 확인
    if [ ! -f "./config/update_manager.txt" ]; then
        error_exit "update_manager.txt not found in ./config directory"
    fi
    
    # Append the new updater configuration from update_manager.txt
    cat "./config/update_manager.txt" >> "$MOONRAKER_CONFIG" || error_exit "Failed to append update manager configuration"
    echo "[OK]"

    # moonraker.asvc 파일 존재 확인
    if [ ! -f "$MOONRAKER_ASVC" ]; then
        touch "$MOONRAKER_ASVC" || error_exit "Failed to create moonraker.asvc"
    fi
    
    # Add service access to Moonraker, if not already present
    echo -n "Checking and updating moonraker.asvc... "
    if ! grep -q "ma3d" "$MOONRAKER_ASVC"; then
        echo -e "\nma3d" >> "$MOONRAKER_ASVC" || error_exit "Failed to update moonraker.asvc"
        echo "[UPDATED]"
    else
        echo "[SKIPPED]"
    fi
}

create_service() {
    # Define the path to the predefined service file
    PREDEFINED_SERVICE_FILE="./config/ma3d.service"
    
    # 서비스 파일 존재 확인
    if [ ! -f "$PREDEFINED_SERVICE_FILE" ]; then
        error_exit "Service file not found at $PREDEFINED_SERVICE_FILE"
    fi

    echo -n "Copying $PREDEFINED_SERVICE_FILE to $MA3D_SERVICE... "
    # Copy the predefined service file to the systemd directory
    sudo cp "$PREDEFINED_SERVICE_FILE" "$MA3D_SERVICE" || error_exit "Failed to copy service file"
    echo "[OK]"

    echo -n "Enabling and starting $MA3D_SERVICE... "
    # Enable and start the service
    sudo systemctl enable ma3d.service || error_exit "Failed to enable ma3d service"
    sudo systemctl start ma3d.service || error_exit "Failed to start ma3d service"
    echo "[OK]"
}

add_config() {
    ORIGINAL_CFG_FILE="./config/MA3D.cfg"
    TARGET_CFG_PATH="${HOME}/printer_data/config/MA3D.cfg"
    
    # 설정 파일 존재 확인
    if [ ! -f "$ORIGINAL_CFG_FILE" ]; then
        error_exit "Configuration file not found at $ORIGINAL_CFG_FILE"
    fi

    CERT_FILE=$(find "./AWS" -name "*.cert.pem" | head -n 1)
    if [ -z "$CERT_FILE" ]; then
        error_exit "No AWS certificate file found in ./AWS"
    fi

    # ID를 전역 변수로 설정
    ID=$(basename "$CERT_FILE" .cert.pem)
    echo "Using AWS Connection ID: $ID"

    cp "$ORIGINAL_CFG_FILE" "$TARGET_CFG_PATH" || error_exit "Failed to copy configuration file"
    sed -i "s/^id:.*$/id: ${ID}/" "$TARGET_CFG_PATH" || error_exit "Failed to update ID in configuration file"
    echo "[OK] Updated 'id' in MA3D.cfg"
}

create_cloudflare_service() {
    echo -n "CloudFlare installation... "

    # Cloudflared 설치 여부 확인
    if ! command -v cloudflared &> /dev/null; then
        error_exit "cloudflared not found. Please install it first."
    fi

    # 터널 존재 여부 확인
    if cloudflared tunnel list | grep -q "printer-$ID"; then
        echo "Tunnel 'printer-$ID' already exists. Skipping creation."
    else
        echo "Creating Cloudflare tunnel with ID 'printer-$ID'..."
        cloudflared tunnel create "printer-$ID" || error_exit "Failed to create Cloudflare tunnel"
    fi

    echo "Cloudflare tunnel setup complete."

    # Find the credentials file
    CREDENTIALS_FILE=$(find "${HOME}/.cloudflared" -type f -name "*.json" | head -n 1)
    if [ -z "$CREDENTIALS_FILE" ]; then
        error_exit "No .json credentials file found!"
    fi

    CONFIG_FILE="/etc/cloudflared/config.yml"

    # 디렉토리 생성 및 config.yml 작성
    sudo mkdir -p /etc/cloudflared || error_exit "Failed to create cloudflared directory"
    # Generate config.yml
    sudo bash -c "cat > $CONFIG_FILE" <<EOL || error_exit "Failed to create config.yml"
tunnel: printer-$ID
credentials-file: $CREDENTIALS_FILE

ingress:
  - hostname: printer-$ID.madeall3d.com
    service: http://localhost:80
  - service: http_status:404
EOL

    # Print result
    echo "Config file generated at $CONFIG_FILE"

    # 인증서 파일 존재 확인
    if [ ! -f "${HOME}/.cloudflared/cert.pem" ]; then
        error_exit "Cloudflare certificate not found at ${HOME}/.cloudflared/cert.pem"
    fi
    
    sudo cp "${HOME}/.cloudflared/cert.pem" /etc/cloudflared/cert.pem || error_exit "Failed to copy Cloudflare certificate"

    cloudflared tunnel route dns printer-$ID printer-$ID.madeall3d.com || error_exit "Failed to configure DNS route"

    # Generate service
    sudo bash -c "cat > /etc/systemd/system/cloudflared.service" <<EOL || error_exit "Failed to create cloudflared service"
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

    sudo systemctl daemon-reload || error_exit "Failed to reload systemd configuration"
    sudo systemctl start cloudflared || error_exit "Failed to start cloudflared service"
    sudo systemctl enable cloudflared || error_exit "Failed to enable cloudflared service"
}

restart_moonraker() {
    echo -n "Restarting Moonraker... "
    sudo systemctl restart moonraker || error_exit "Failed to restart Moonraker"
    echo "[OK]"
}

# Run steps
verify_not_root
check_directories
add_updater
create_service
add_config
create_cloudflare_service
restart_moonraker

echo "MA3D installation completed successfully!"
