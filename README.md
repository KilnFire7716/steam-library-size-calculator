# Steam Library Size Calculator

Python tool that calculates the exact total storage space required to install your entire Steam library (including Steam Family Sharing games). It does this through the Steam appinfo.vdf cache locally on your device. You can **optionally utilize your Steam API key and account ID to act as an audit check against your local appinfo.vdf cache in the instance it isn't complete. Testing against my own library worked fine with no API key and is more private so that is my default recommendation to get a quick idea.

### Why Does This Exist?
When you select all games in your Steam client and click **Install**, Steam immediately blocks the dialog with a `"Not enough free disk space"` error if the combined size exceeds your physical drive's free space—refusing to show you the total storage required.

This script parses Steam's local binary depot cache (`appinfo.vdf`) directly using Python's built-in standard library (`struct`), giving you a calculation across **Windows**, **macOS**, and **Linux / SteamOS**.

---

## Features
* **Zero External Dependencies:** Uses only built-in Python 3 modules (`os`, `struct`, `json`, `urllib`, `winreg`).
* **Cross-Platform Auto-Detection:** Automatically locates your `Steam/appcache/appinfo.vdf` file on Windows (via Registry & standard paths), macOS, and Linux/SteamOS (Native, Flatpak, and Snap).
* **Supports Binary VDF v27, v28, and v29+:** Includes a built-in binary parser with string table support for Valve's latest `appinfo.vdf` format.
* **Largest Games Breakdown:** Lists the top 10 largest games in your library by default.

---

## Step 1: Steam Client Local Cache Setup (Important!)
By default, Steam only caches depot metadata in `appinfo.vdf` for games your Steam client application has interacted with. To make sure **100% of your owned and Family Shared games** are cached before running the script:

1. Open the **Steam** desktop client and go to your **Library**.
2. Click the very first game in your list, scroll to the bottom of your library, hold **Shift**, and then click the very last game so your entire library is highlighted. Right-click and click "Install selected".
3. Wait **10–15 seconds**.

---

## Step 2: How to Run the Script on Each OS

### Windows
1. Ensure [Python 3](https://www.python.org/downloads/windows/) is installed.
2. Open **PowerShell** or **Command Prompt** in the folder containing `steam_library_size.py`.
3. Run:
   ```powershell
   python steam_library_size_calculator.py
   ```
   *(Note: The script automatically checks the Windows Registry `HKCU\Software\Valve\Steam` to find your Steam folder, even if Steam is installed on a secondary drive like `D:\Steam`).*

### macOS
1. Open **Terminal** in the folder containing `steam_library_size.py`.
2. Run:
   ```bash
   python3 steam_library_size_calculator.py
   ```
   *(Looks in `~/Library/Application Support/Steam/appcache/appinfo.vdf` by default).*

### Linux & Steam Deck (SteamOS)
1. Open your terminal (**Konsole** in Desktop Mode on Steam Deck).
2. Run:
   ```bash
   python3 steam_library_size_calculator.py
   ```
   *(Automatically checks `~/.steam/steam`, `~/.local/share/Steam`, Flatpak `~/.var/app/com.valvesoftware.Steam/...`, and Snap directories).*

---

## Optional Command-Line Arguments

| Argument | Description | Example |
| :--- | :--- | :--- |
| `--top N` | Show the top `N` largest games in your library (default: `10`). Set to `0` to hide. | `python3 steam_library_size.py --top 25` |
| `--steam-path` | Manually specify a custom Steam installation directory. | `python3 steam_library_size.py --steam-path "E:\Steam"` |
| `--api-key` | Optional Steam Web API Key from [steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey). | `python3 steam_library_size.py --api-key YOUR_KEY --steam-id YOUR_ID` |
| `--steam-id` | Your 17-digit `SteamID64` (used alongside `--api-key`). | See above |
