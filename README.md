# MA3D

## Introduction

MA3D is a Klipper plugin designed to enhance the 3D printing experience for users of MA3D 3D printers. It integrates seamlessly with Klipper and Moonraker, providing additional features and capabilities.

## Prerequisites

Before installing the MA3D plugin, ensure that both Klipper and Moonraker are already installed and running on your system. This plugin requires these components to function properly.

## Installation

To install the MA3D plugin, follow these steps:

1. **Clone the Repository**

```
git clone https://oauth2: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@github.com/MadeAll/MA3D.git
```

2. **Run the Installation Script**

Navigate to the cloned repository directory and execute the install script:

```
cd MA3D
./install.sh
```

This script automates the setup process, including updating the Moonraker configuration and setting up a systemd service for the MA3D plugin.

3. **Verify Installation**

Check the status of the MA3D service to ensure it is active and running:

```
systemctl status ma3d.service
```

By completing these steps, you will have successfully installed the MA3D plugin on your system.
