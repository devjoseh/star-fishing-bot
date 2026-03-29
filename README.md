# 🎣 Star Fishing Bot

> Automation bot for the Star Fishing minigame. Detects the fishing bar, automatically casts the line at the right moment, and auto-sells your stars when the inventory is full.

> [!IMPORTANT]
> **This project is strictly educational.** It was developed for **learning** purposes in task automation, computer vision with OpenCV, and Python scripting. It is not intended to provide a competitive advantage in any online environment. Use at your own risk.

---

## Installation

Requires **Python 3.10+** and **Windows**.

```bash
git clone https://github.com/devjoseh/star-fishing-bot.git
cd star-fishing-bot
pip install -r requirements.txt
```

---

## How It Works

The bot monitors a configurable region of your screen for the green fishing bar. When detected, it:

1. **Releases** the held mouse button to start the cast.
2. **Holds** the left mouse button for `hold_time` seconds (filling the bar to the top).
3. **Releases** to cast the line into the water.
4. **Resumes holding** the mouse waiting for the next bar to appear.
5. **Auto-Sells** *(optional)*: If the "Inventory Full" alert appears while waiting, the bot automatically opens the backpack (Key `3`), clicks "Sell All", and resumes fishing (Key `1`). This can be toggled on/off in the Control Panel.

```
🖱 Hold (waiting) → ✅ Green detected → 🎣 Cast (hold_time) → 🖱 Hold again
🎒 Inventory Full detected → 🛑 Release → ⌨️ Press 3 → 🖱 Click Sell → ⌨️ Press 1 → 🖱 Hold again
```

---

## Setup & Usage

### 1. Configure Screen Regions (first time only)

With the game open in Borderless/Fullscreen mode, run:

```bash
python launcher.py
```

Click **Configure Regions**. A menu will open with 3 buttons. Configure all 3 regions:

1. **Fishing Bar** — drag a box over where the fishing power bar appears on screen.
2. **Inventory Full Message** — wait for your inventory to fill up, then drag a box over the red "Inventory Full" text. The tool will extract its shape as a visual template.
3. **Sell All Button** — open your backpack in-game and drag a box directly over the green "Sell All" button.

Click **Save ROI** (or press **S / Enter**) after each selection.

> See [Tips for Best Detection](#tips-for-best-detection) before configuring — proper setup makes a big difference.

### 2. Run the bot

```bash
python launcher.py
```

Click **Start Bot**. The Control Panel window will open. Adjust any settings there — all changes are saved automatically.

| Key | Action |
|-----|--------|
| `F6` | Start fishing loop |
| `F7` | Stop fishing loop |
| `Ctrl+C` | Exit the script (terminal) |

> Make sure the **game window is focused** when you press `F6`.

---

## Tips for Best Detection

The fishing bar detector works by counting green pixels in the configured region. A few in-game adjustments significantly improve reliability:

- **Zoom out to the maximum** — a zoomed-out view has fewer on-screen elements, reducing false positives from other green objects in the scene.
- **Move the camera so the fishing bar sits against a dark background** — the detection is most accurate when there is low contrast around the bar area. Aim for a wall, dark floor, or shadowed surface behind it.
- **Set game graphics to the lowest possible setting** — lower graphics reduce visual noise (particles, ambient effects, shadows) that could interfere with pixel detection.

Applying all three of these before configuring will give you the most reliable region configuration.

---

## Configuration

`config.json` is generated automatically by `roi_selector.py` and lives only on your machine (it is not committed to the repository). All behavioral settings can be adjusted live in the **Control Panel** without editing the file manually.

| Field | Default | Description |
|-------|---------|-------------|
| `roi` | *(generated)* | Screen region where the fishing power bar appears |
| `inventory_roi` | *(generated)* | Screen region where the "Inventory Full" text appears |
| `sell_button_roi` | *(generated)* | Screen region for the Sell All button |
| `hold_time` | `0.58` | Seconds to hold mouse while casting |
| `start_key` | `F6` | Hotkey to start the fishing loop |
| `stop_key` | `F7` | Hotkey to stop the fishing loop |
| `green_threshold` | `10` | Minimum green pixels to detect the bar as ready |
| `poll_interval` | `0.1` | Screen check interval in seconds |
| `post_cast_delay` | `0.1` | Pause between cast release and holding again |
| `auto_sell_enabled` | `true` | Auto-sell stars when inventory is full |
| `inactive_pause_enabled` | `false` | Pause the bot if the fishing area goes inactive |
| `inactive_pause_triggers` | `5` | Rapid cast rejections before triggering the pause |
| `inactive_pause_duration` | `1` | Minutes to sleep when the area is inactive |
| `inactive_cast_time_threshold` | `6.0` | Max seconds between casts to count as a fast rejection |

> **Tuning tip:** If the bar doesn't reach the top, decrease `hold_time`. If it overshoots, increase it slightly.

---

## Project Structure

```
star-fishing/
├── src/
│   ├── automator.py   # Main loop (state machine)
│   ├── vision.py      # Screen capture & green pixel detection
│   ├── inputs.py      # Mouse hold/release + hotkey listener
│   ├── config.py      # Config loader/saver
│   └── settings_ui.py # Control panel UI
├── locales/
│   ├── pt.json        # Portuguese translations
│   └── en.json        # English translations
├── assets/            # Visual templates (auto-generated)
├── launcher.py        # Entry point (launcher UI)
├── main.py            # Bot startup logic
├── roi_selector.py    # Visual region configuration tool
└── requirements.txt
```

---

## Disclaimer

This bot is intended for personal, educational use. Automated gameplay may violate the terms of service of the game. Use at your own risk.
