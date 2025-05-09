# MA3D

## Introduction

MA3D is a Klipper plugin designed to enhance the 3D printing experience for users of MA3D 3D printers. It integrates seamlessly with Klipper, Moonraker providing additional features and capabilities.

## Prerequisites

If using CB2 and Mininal OS Image, add user first.
```
sudo adduser biqu
sudo usermod -aG sudo biqu
```
Before installing the MA3D plugin, ensure that both Klipper and Moonraker are already installed and running on your system. This plugin requires these components to function properly.
```
sudo apt-get update && sudo apt-get install git -y
```
```
cd ~ && git clone https://github.com/dw-0/kiauh.git
```
```
./kiauh/kiauh.sh
```

## Device Wifi Connect

Make system.cfg wifi connection as SSID "@naneunguccida" PW "jimmy001224".
or use nmcli device wifi connect "@naneunguccida" password jimmy001224
Connect device to Mobile Hotspot. (WPA2 Required)

Set wifi priority to High value
```
nmcli con modify @naneunguccida connection.autoconnect-priority 10
nmcli con show @naneunguccida | grep autoconnect-priority
```

Check current connection. Hotspot wifi must connected.
```
nmcli con show
```

Check Wifi list
```
nmcli device wifi list
```

Connect to new Wifi
```
nmcli device wifi connect "KHU Wi-Fi Guest" password vision2020
```

If "New Connection activation was enqueued", it means connection is ready.
send "sudo reboot" to enable new connection. ( Turn hotspot off )

When you need change static ip
```
nmcli connection modify "MadeAll 24Ghz" ipv4.addresses "192.168.1.{num}/24" ipv4.gateway "192.168.1.1" ipv4.dns "8.8.8.8" ipv4.method "manual"
```
## Installation

To install the MA3D plugin, follow these steps:

1. **Clone the Repository**

```
git clone https://github.com/MadeAll/MA3D.git
```

2. **ADD CloudFlare DNS**

Add Printer at web page, and copy the Device ID.
Install CloudFlared for tunneling service.
Login Cloudflare Service (Login As gucciheon@gmail.com)
```
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm
chmod +x cloudflared-linux-arm
sudo mv cloudflared-linux-arm /usr/local/bin/cloudflared
cloudflared tunnel login
```
After login to cloudflare, Add dns service.

3. **Run the Installation Script**

Navigate to the cloned repository directory and execute the install script:

```
cd MA3D && bash ./install.sh ID=your_id_value
```

This script automates the setup process, including updating the Moonraker configuration and setting up a systemd service for the MA3D plugin.

4. **Verify Installation**

Check the status of the MA3D service to ensure it is active and running:

```
systemctl status cloudflared
systemctl status ma3d.service
```

By completing these steps, you will have successfully installed the MA3D plugin on your system.
