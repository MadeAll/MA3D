MOONRAKER_CONFIG="${HOME}/printer_data/config/moonraker.conf"
MOONRAKER_FALLBACK="${HOME}/klipper_config/moonraker.conf"
SYSTEMDDIR="/etc/systemd/system"
KLIPPER_PATH="${HOME}/klipper"
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/ && pwd )"

add_updater()
{
    echo -n "Adding update manager to moonraker.conf... "
    update_section=$(grep -c '\[update_manager[a-z ]* MA3D\]' $MOONRAKER_CONFIG || true)
    if [ "$update_section" -eq 0 ]; then
        echo -e "\n[update_manager MA3D]" >> "$MOONRAKER_CONFIG"
        echo "type: git_repo" >> "$MOONRAKER_CONFIG"
        echo "path: ${SRCDIR}" >> "$MOONRAKER_CONFIG"
        echo "origin: https://oauth2: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@github.com/MadeAll/MA3D.git" >> "$MOONRAKER_CONFIG"
        echo -e "\n" >> "$MOONRAKER_CONFIG"
        echo "[OK]"

        echo -n "Restarting Moonraker... "
        sudo systemctl restart moonraker
        echo "[OK]"
    else
        echo "[SKIPPED]"
    fi
}

# Run steps
add_updater  
