# MA3D

## Introduction

MA3D is a Klipper plugin designed to enhance the 3D printing experience for users of MA3D 3D printers. It integrates seamlessly with Klipper and Moonraker, providing additional features and capabilities.

## Prerequisites

Before installing the MA3D plugin, ensure that both Klipper and Moonraker are already installed and running on your system. This plugin requires these components to function properly.

## Device Wifi Connect

Make system.cfg wifi connection as SSID "@naneunguccida" PW "jimmy001224".
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
nmcli device wifi connect "SSID" password PWD
```

If "New Connection activation was enqueued", it means connection is ready.
send "sudo reboot" to enable new connection. ( Turn hotspot off )

When you need change static ip
```
nmcli connection modify "MyWiFiConnection" ipv4.addresses "192.168.1.{num}/24" ipv4.gateway "192.168.1.1" ipv4.dns "8.8.8.8" ipv4.method "manual"
```

## Installation

To install the MA3D plugin, follow these steps:

1. **Clone the Repository**

```
git clone https://oauth2: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@github.com/MadeAll/MA3D.git
```

2. **ADD AWS IoT Certs**

Add Printer at web page, create device in AWS by same id
Upload connect_device_package.zip File to MA3D/AWS

```
cd MA3D/AWS && sh ./install.sh
```

After AWS MQTT Connection checked, Press Ctrl+C to kill Program.

3. **Run the Installation Script**

Navigate to the cloned repository directory and execute the install script:

```
cd .. && sh ./install.sh
```

This script automates the setup process, including updating the Moonraker configuration and setting up a systemd service for the MA3D plugin.

4. **Verify Installation**

Check the status of the MA3D service to ensure it is active and running:

```
systemctl status ma3d.service
```

By completing these steps, you will have successfully installed the MA3D plugin on your system.
