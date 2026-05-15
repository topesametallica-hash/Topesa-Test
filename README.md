# Raspberry Pi Relay Touchscreen App

Touchscreen-friendly Python/Kivy app for controlling GPIO relay modules on Raspberry Pi.

## Hardware defaults

- Relay 1: BCM GPIO 17
- Relay 2: BCM GPIO 27
- Relay 3: BCM GPIO 22
- Relay 4: BCM GPIO 23
- Relay logic: active-low

Edit `relays.json` to rename relays, change pins, or set `active_low` to `false` for active-high relay boards.

## Install on Raspberry Pi

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-kivy
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements.txt
```

If Kivy is already installed through apt, the `pip install` step can be skipped except for `RPi.GPIO`.

## Run

```bash
source .venv/bin/activate
python main.py
```

For a windowed test instead of fullscreen:

```bash
RELAY_FULLSCREEN=0 python main.py
```

For demo mode without GPIO:

```bash
RELAY_DEMO=1 RELAY_FULLSCREEN=0 python main.py
```

## Autostart from desktop

Create `~/.config/autostart/relay-control.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Relay Control
Exec=/bin/bash -lc 'cd /home/pi/relay-control && source .venv/bin/activate && python main.py'
Terminal=false
```

Change `/home/pi/relay-control` to the folder where this project lives.
