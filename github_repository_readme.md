# Steam Library Size Calculator

A zero-dependency Python tool that calculates the exact total storage space required to install your entire Steam library (including Steam Family Sharing games).

### Why Does This Exist?
When you select all games in your Steam client and click **Install**, Steam immediately blocks the dialog with a `"Not enough free disk space"` error if the combined size exceeds your physical drive's free space—refusing to show you the total storage required. Furthermore, web-based calculators rely on outdated text strings from Steam Store system requirement pages rather than live depot manifests, typically underreporting library sizes by 15–25%.

This script parses Steam's local binary depot cache (`appinfo.vdf`) directly using Python's built-in standard library (`struct`), giving you an accurate byte-for-byte calculation across **Windows**, **macOS**, and **Linux / SteamOS**.

---

## Features
* **Zero External Dependencies:** Uses only built-in Python 3 modules (`os`, `struct`, `json`, `urllib`, `winreg`). No `pip install` or virtual environments needed.
* **Cross-Platform Auto-Detection:** Automatically locates your `Steam/appcache/appinfo.vdf` file on Windows (via Registry & standard paths), macOS, and Linux/SteamOS (Native, Flatpak, and Snap).
* **Supports Binary VDF v27, v28, and v29+:** Includes a built-in binary parser with string table support for Valve's latest `appinfo.vdf` format.
* **Largest Games Breakdown:** Lists the top 10 largest games in your library by default.

---

## Step 1: Prime Your Steam Client Cache (Important!)
By default, Steam only caches depot metadata in `appinfo.vdf` for games your client has interacted with. To make sure **100% of your owned and Family Shared games** are cached before running the script:

1. Open the **Steam** desktop client and go to your **Library**.
2. Make sure **Games** (and **Include games from Family Library**, if desired) is enabled in the top left filter dropdown.
3. Click the very first game in your list, scroll to the bottom, hold **Shift**, and click the very last game so your entire library is highlighted.
4. Wait **10–15 seconds**. Simply highlighting all games forces Steam's background client worker to download and write all depot manifests into `appinfo.vdf`.

---

## Step 2: How to Run the Script on Each OS

### Windows
1. Ensure [Python 3](https://www.python.org/downloads/windows/) is installed.
2. Open **PowerShell** or **Command Prompt** in the folder containing `steam_library_size.py`.
3. Run:
   ```powershell
   python steam_library_size.py
   ```
   *(Note: The script automatically checks the Windows Registry `HKCU\Software\Valve\Steam` to find your Steam folder, even if Steam is installed on a secondary drive like `D:\Steam`).*

### macOS
1. Open **Terminal** in the folder containing `steam_library_size.py`.
2. Run:
   ```bash
   python3 steam_library_size.py
   ```
   *(Looks in `~/Library/Application Support/Steam/appcache/appinfo.vdf` by default).*

### Linux & Steam Deck (SteamOS)
1. Open your terminal (**Konsole** in Desktop Mode on Steam Deck).
2. Run:
   ```bash
   python3 steam_library_size.py
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

---

## Alternative Method: The 64 TB Virtual Drive Trick (No Script Needed)
If you want the Steam client GUI itself to calculate the combined installation total, you can mount a thin-provisioned **64 TB virtual drive** that uses almost zero real disk space (~20–150 MB) and add it as a Steam Storage folder:

### On Windows (VHDX)
1. Right-click the **Start** button and open **Disk Management**.
2. Click **Action** -> **Create VHD**.
3. Save it anywhere as `SteamCheck.vhdx`, set size to **64 TB**, select **VHDX**, and select **Dynamically expanding**.
4. Right-click the new disk in the bottom pane -> **Initialize Disk** (GPT), then right-click the unallocated space -> **New Simple Volume** (Quick Format NTFS as drive `Z:`).
5. In Steam, go to **Steam** -> **Settings** -> **Storage** -> **Add Drive** (`Z:`), select all games in your library, click **Install**, and select `Z:` to see the exact space required. Cancel the install, detach the VHD in Disk Management, and delete the `.vhdx` file.

### On macOS (APFS Sparsebundle)
1. Run this in **Terminal** to create and mount a 64 TB sparse disk image:
   ```bash
   hdiutil create -size 64t -type SPARSEBUNDLE -fs APFS -volname "SteamCheck" ~/Desktop/SteamCheck.sparsebundle
   open ~/Desktop/SteamCheck.sparsebundle
   ```
2. Add `/Volumes/SteamCheck` under **Steam** -> **Settings** -> **Storage**, select all games, and click **Install** to view the total. Eject and delete `SteamCheck.sparsebundle` when done.

### On Linux / SteamOS (Sparse Loopback Image)
1. Create and mount a 64 TB sparse ext4 file in your terminal:
   ```bash
   truncate -s 64T /tmp/steam_check.img
   mkfs.ext4 -F -O sparse_super2 /tmp/steam_check.img
   mkdir -p /tmp/steam_mount
   sudo mount -o loop /tmp/steam_check.img /tmp/steam_mount
   ```
2. Add `/tmp/steam_mount` in Steam Storage Settings to check your total, then clean up:
   ```bash
   sudo umount /tmp/steam_mount && rm -rf /tmp/steam_check.img /tmp/steam_mount
   ```