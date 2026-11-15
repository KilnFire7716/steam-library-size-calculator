#!/usr/bin/env python3
"""
Steam Library Size Calculator (Cross-Platform: Windows, macOS, Linux / SteamOS)
Parses Steam's local binary appinfo.vdf cache to calculate the total uncompressed
install size of your Steam library (including Family Sharing games cached locally).
Zero external pip dependencies required!
"""

import os
import sys
import platform
import struct
import json
import urllib.request
import argparse

# Optional: Set default Steam Web API Key and 17-digit SteamID64 here, or pass via CLI flags
DEFAULT_API_KEY = ""
DEFAULT_STEAM_ID = ""


def get_default_steam_path():
    """Auto-detects the default Steam installation directory based on the current OS."""
    system = platform.system().lower()

    if system == "windows":
        # Check Windows Registry first for a custom Steam install location
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
            winreg.CloseKey(key)
            if os.path.exists(steam_path):
                return os.path.normpath(steam_path)
        except Exception:
            pass

        # Fallback to standard Windows paths
        candidates = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam"),
            os.path.expandvars(r"%ProgramFiles%\Steam"),
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
        ]
    elif system == "darwin":
        # macOS standard path
        candidates = [
            os.path.expanduser("~/Library/Application Support/Steam"),
        ]
    else:
        # Linux & SteamOS (Standard, Debian/Ubuntu, Flatpak, and Snap paths)
        candidates = [
            os.path.expanduser("~/.steam/steam"),
            os.path.expanduser("~/.local/share/Steam"),
            os.path.expanduser("~/.var/app/com.valvesoftware.Steam/.local/share/Steam"),
            os.path.expanduser("~/snap/steam/common/.local/share/Steam"),
        ]

    for path in candidates:
        if os.path.exists(os.path.join(path, "appcache", "appinfo.vdf")):
            return path

    return candidates[0]


def read_cstring(buf, pos):
    """Reads a null-terminated UTF-8 string from a binary buffer."""
    end = buf.find(b"\x00", pos)
    return buf[pos:end].decode("utf-8", errors="replace"), end + 1


def parse_bin_vdf(buf, pos, string_table=None):
    """Recursively parses Valve's binary VDF dictionary format."""
    obj = {}
    while pos < len(buf):
        t = buf[pos]
        pos += 1

        # 0x08 marks the end of the current dictionary/object
        if t == 0x08:
            break

        # v29+ uses a string table index (4-byte uint32) for keys; older versions use inline strings
        if string_table is not None:
            idx = struct.unpack_from("<I", buf, pos)[0]
            pos += 4
            key = string_table[idx]
        else:
            key, pos = read_cstring(buf, pos)

        # Decode value based on data type byte
        if t == 0x00:      # Nested Dictionary
            obj[key], pos = parse_bin_vdf(buf, pos, string_table)
        elif t == 0x01:    # UTF-8 String
            obj[key], pos = read_cstring(buf, pos)
        elif t == 0x02:    # Int32 (4 bytes)
            obj[key] = struct.unpack_from("<i", buf, pos)[0]
            pos += 4
        elif t == 0x03:    # Float32 (4 bytes)
            obj[key] = struct.unpack_from("<f", buf, pos)[0]
            pos += 4
        elif t == 0x04:    # Pointer (4 bytes)
            obj[key] = struct.unpack_from("<I", buf, pos)[0]
            pos += 4
        elif t == 0x05:    # UTF-16 Wide String
            end = pos
            while buf[end : end + 2] != b"\x00\x00":
                end += 2
            obj[key] = buf[pos:end].decode("utf-16-le", errors="replace")
            pos = end + 2
        elif t == 0x06:    # Color (4 bytes)
            obj[key] = struct.unpack_from("<I", buf, pos)[0]
            pos += 4
        elif t == 0x07:    # UInt64 (8 bytes)
            obj[key] = struct.unpack_from("<Q", buf, pos)[0]
            pos += 8

    return obj, pos


def fetch_owned_games_api(api_key, steam_id):
    """Fetches owned game AppIDs from the official Steam Web API."""
    api_apps = set()
    url = (
        f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
        f"?key={api_key}&steamid={steam_id}&include_appinfo=1&include_played_free_games=1"
    )
    try:
        req = urllib.request.urlopen(url, timeout=15)
        resp = json.loads(req.read().decode("utf-8"))
        for g in resp.get("response", {}).get("games", []):
            api_apps.add(g["appid"])
        print(f"[+] Steam Web API returned {len(api_apps)} owned games.")
    except Exception as e:
        print(f"[!] Warning: Could not fetch from Steam Web API: {e}")
    return api_apps


def main():
    parser = argparse.ArgumentParser(
        description="Calculate the total storage size required for your Steam Library."
    )
    parser.add_argument(
        "--steam-path",
        type=str,
        default=get_default_steam_path(),
        help="Path to your Steam installation folder (auto-detected by default)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=DEFAULT_API_KEY,
        help="Optional Steam Web API Key",
    )
    parser.add_argument(
        "--steam-id",
        type=str,
        default=DEFAULT_STEAM_ID,
        help="Optional 17-digit SteamID64",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Display the top N largest games found (default: 10)",
    )
    args = parser.parse_args()

    appinfo_path = os.path.join(args.steam_path, "appcache", "appinfo.vdf")

    print(f"[*] Detected OS: {platform.system()} ({platform.release()})")
    print(f"[*] Looking for appinfo.vdf at: {appinfo_path}")

    if not os.path.exists(appinfo_path):
        print("\n[!] Error: Could not find appinfo.vdf at the path above.")
        print("    Make sure Steam is installed and you have logged in at least once,")
        print('    or pass your custom path via: python steam_library_size.py --steam-path "/path/to/Steam"')
        sys.exit(1)

    api_apps = set()
    if args.api_key and args.steam_id:
        api_apps = fetch_owned_games_api(args.api_key, args.steam_id)

    with open(appinfo_path, "rb") as f:
        data = f.read()

    magic, universe = struct.unpack_from("<II", data, 0)
    version = magic & 0xFF
    pos = 8

    string_table = None
    if version >= 29:
        st_offset = struct.unpack_from("<Q", data, pos)[0]
        pos += 8
        st_count = struct.unpack_from("<I", data, st_offset)[0]
        st_pos = st_offset + 4
        string_table = []
        for _ in range(st_count):
            s, st_pos = read_cstring(data, st_pos)
            string_table.append(s)

    total_bytes = 0
    counted_games = 0
    games_list = []

    while pos < len(data):
        appid = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        if appid == 0:
            break

        size = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        next_entry = pos + size

        header_skip = 4 + 4 + 8 + 20 + 4 + (20 if version >= 28 else 0)
        app_dict, _ = parse_bin_vdf(data, pos + header_skip, string_table)
        app_data = app_dict.get("appinfo", {})
        common = app_data.get("common", {})

        if isinstance(common, dict) and common.get("type", "").lower() == "game":
            game_name = common.get("name", f"AppID {appid}")
            depots = app_data.get("depots", {})
            game_bytes = 0

            if isinstance(depots, dict):
                for depot_id, depot_info in depots.items():
                    if not str(depot_id).isdigit() or not isinstance(depot_info, dict):
                        continue
                    config = depot_info.get("config", {})
                    oslist = config.get("oslist", "windows") if isinstance(config, dict) else "windows"

                    # Count primary Windows/shared depots to prevent double-counting macOS/Linux builds
                    if "windows" in oslist:
                        manifests = depot_info.get("manifests", {})
                        pub = manifests.get("public", {}) if isinstance(manifests, dict) else {}
                        d_size = pub.get("size") if isinstance(pub, dict) else depot_info.get("maxsize", 0)
                        if d_size:
                            game_bytes += int(d_size)

            if game_bytes > 0:
                total_bytes += game_bytes
                counted_games += 1
                games_list.append((game_name, appid, game_bytes))

        pos = next_entry

    gib = total_bytes / (1024 ** 3)
    tib = total_bytes / (1024 ** 4)
    gb = total_bytes / (1000 ** 3)
    tb = total_bytes / (1000 ** 4)

    print("\n" + "=" * 60)
    print(f"Counted Games in Cache : {counted_games}")
    print(f"Total Binary Size      : {gib:,.2f} GiB ({tib:,.2f} TiB)")
    print(f"Total Decimal Size     : {gb:,.2f} GB  ({tb:,.2f} TB)")
    print("=" * 60)

    if args.top > 0 and games_list:
        games_list.sort(key=lambda x: x[2], reverse=True)
        print(f"\nTop {min(args.top, len(games_list))} Largest Games in Library:")
        print("-" * 60)
        for idx, (name, appid, b_size) in enumerate(games_list[: args.top], 1):
            g_gib = b_size / (1024 ** 3)
            print(f"{idx:2d}. {name[:40]:<40} | {g_gib:7.2f} GiB")


if __name__ == "__main__":
    main()
