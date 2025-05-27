import argparse
import requests
import json
import base64
import os
import re
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import zipfile
import glob
from datetime import datetime

# By: SecurityBreached
# https://whoami.securitybreached.org/
# Muhammad Khizer Javed
# khizerjaved@securitybreached.org

# --- API Configuration ---
NEW_TOKEN_URL = "https://token.mi9.com/"
NEW_API_URL = "https://api.mi9.com/get"
NEW_GET_VERSION_URL = "https://api.mi9.com/get-version"
NEW_DEFAULT_SDK = 30
NEW_API_COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Sec-Ch-Ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
}
NEW_HEADERS_TOKEN = {**NEW_API_COMMON_HEADERS, "Accept": "*/*", "Content-Type": "application/json", "Origin": "https://mi9.com", "Referer": "https://mi9.com/", "Priority": "u=1, i", "Sec-Fetch-Site": "same-site", "Connection": "keep-alive"}
NEW_HEADERS_API_GET = {**NEW_API_COMMON_HEADERS, "Accept": "text/event-stream", "Origin": "https://mi9.com", "Referer": "https://mi9.com/", "Sec-Fetch-Site": "same-site", "Connection": "keep-alive"}
NEW_HEADERS_GET_VERSION = {**NEW_API_COMMON_HEADERS, "Accept": "*/*", "Content-Type": "application/json", "Origin": "https://mi9.com", "Referer": "https://mi9.com/", "Sec-Fetch-Site": "same-site", "Connection": "keep-alive"}

# OLD API (apk.ad based)
OLD_TOKEN_URL = "https://token.apk.ad/"
OLD_API_URL = "https://api.apk.ad/get"
OLD_GET_VERSION_URL = "https://api.apk.ad/get-version"
OLD_DEFAULT_SDK = "default"
OLD_HEADERS_TOKEN = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0", "Accept": "*/*", "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br", "Referer": "https://apkdownloader.pages.dev/", "Content-Type": "application/json",
    "Origin": "https://apkdownloader.pages.dev", "Connection": "keep-alive"
}
OLD_HEADERS_API_GET = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0", "Accept": "text/event-stream", "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br", "Referer": "https://apkdownloader.pages.dev/", "Origin": "https://apkdownloader.pages.dev", "Connection": "keep-alive"
}
OLD_HEADERS_GET_VERSION = OLD_HEADERS_API_GET.copy(); OLD_HEADERS_GET_VERSION["Accept"] = "*/*"; OLD_HEADERS_GET_VERSION["Content-Type"] = "application/json"


# --- General Configuration ---
PLAY_URL = "https://play.google.com/store/apps/details?id="
OUTPUT_BASE_DIR = "apk_downloads"
TOOL_NAME = "PlayRetrieve"
TOOL_VERSION = "1.2.7"
Author_Name = "Muhammad Khizer Javed"
Author_URL = "whoami.securitybreached.org"

BANNER = rf"""

  ___ _           ___     _       _
 | _ \ |__ _ _  _| _ \___| |_ _ _(_)_____ _____
 |  _/ / _` | || |   / -_)  _| '_| / -_) V / -_)
 |_| |_\__,_|\_, |_|_\___|\__|_| |_\___|\_/\___|
             |__/
              {TOOL_NAME} v{TOOL_VERSION}
{Author_Name} | {Author_URL}
----------------------------------------------------
"""

PROC_SUCCESS = "SUCCESS"
PROC_SKIPPED_EXISTING = "SKIPPED_EXISTING"
PROC_FAILED = "FAILED"

CURRENT_API_CONFIG = {}
args_global = None # Changed from args to args_global to avoid conflict with local args in functions

def get_api_display_name(verbose_flag):
    if not CURRENT_API_CONFIG: return "Unknown API"
    return CURRENT_API_CONFIG['name'] if verbose_flag else CURRENT_API_CONFIG['short_name']

def set_api_config(preference):
    if preference == "new":
        return {
            "name": "New API (mi9.com)", "short_name": "API 1 (mi9)",
            "TOKEN_URL": NEW_TOKEN_URL, "API_URL": NEW_API_URL, "GET_VERSION_URL": NEW_GET_VERSION_URL,
            "DEFAULT_SDK": NEW_DEFAULT_SDK, "HEADERS_TOKEN": NEW_HEADERS_TOKEN,
            "HEADERS_API_GET": NEW_HEADERS_API_GET, "HEADERS_GET_VERSION": NEW_HEADERS_GET_VERSION
        }
    elif preference == "old":
        return {
            "name": "Old API (apk.ad)", "short_name": "API 2 (apk.ad)",
            "TOKEN_URL": OLD_TOKEN_URL, "API_URL": OLD_API_URL, "GET_VERSION_URL": OLD_GET_VERSION_URL,
            "DEFAULT_SDK": OLD_DEFAULT_SDK, "HEADERS_TOKEN": OLD_HEADERS_TOKEN,
            "HEADERS_API_GET": OLD_HEADERS_API_GET, "HEADERS_GET_VERSION": OLD_HEADERS_GET_VERSION
        }
    print(f"[!] Invalid API preference '{preference}', defaulting to 'new'.")
    return set_api_config("new")

def extract_package_id(play_store_url):
    if not play_store_url or not play_store_url.startswith(PLAY_URL):
        return None
    parsed_url = urlparse(play_store_url)
    if parsed_url.netloc not in ["play.google.com", "www.play.google.com"]:
        return None
    query_params = parse_qs(parsed_url.query)
    return query_params.get('id', [None])[0]

def get_api_token_attempt(api_config_to_try, package_id, device, arch, vc, sdk_val_for_api, verbose_flag):
    api_name_display = api_config_to_try['name'] if verbose_flag else api_config_to_try['short_name']
    payload = {"package": package_id, "device": device, "arch": arch, "vc": vc, "device_id": "", "sdk": sdk_val_for_api}
    try:
        print(f"[*] Attempting token request with {api_name_display} for {package_id} (vc:{vc}, sdk:{sdk_val_for_api})...")
        response = requests.post(api_config_to_try['TOKEN_URL'], headers=api_config_to_try['HEADERS_TOKEN'], json=payload, timeout=20)
        try: data = response.json()
        except json.JSONDecodeError as e:
            if verbose_flag: print(f"[!] ({api_name_display}) FAILED TO DECODE JSON (TOKEN) for {package_id} (vc:{vc},sdk:{sdk_val_for_api}) (Error: {e}). Status: {response.status_code}\nText: {response.text}")
            else: print(f"[!] ({api_name_display}) Failed to decode token response for {package_id}.")
            return None, None
        response.raise_for_status()
        return (data.get("token"), data.get("timestamp")) if data.get("success") else (None, None)
    except requests.exceptions.RequestException as e:
        print(f"[!] ({api_name_display}) Error requesting token for {package_id} (vc:{vc},sdk:{sdk_val_for_api}): {e}")
        return None, None

def get_api_token(package_id, device="phone", arch="arm64-v8a", vc="0", sdk_version_arg=None):
    global CURRENT_API_CONFIG, args_global
    api_order = [args_global.api_preference] # Use args_global
    if args_global.api_preference == "new" and "old" not in api_order : api_order.append("old")
    elif args_global.api_preference == "old" and "new" not in api_order : api_order.append("new")

    for api_pref_key in api_order:
        api_config_to_try = set_api_config(api_pref_key)
        sdk_to_use_for_api = sdk_version_arg if sdk_version_arg is not None else api_config_to_try['DEFAULT_SDK']
        token, timestamp = get_api_token_attempt(api_config_to_try, package_id, device, arch, vc, sdk_to_use_for_api, args_global.verbose) # Pass verbose
        if token and timestamp:
            CURRENT_API_CONFIG = api_config_to_try
            print(f"[+] Successfully obtained token using {get_api_display_name(args_global.verbose)}.") # Use args_global.verbose
            return token, timestamp, sdk_to_use_for_api
    print(f"[!!!] Failed to get token for {package_id} using all available APIs.")
    return None, None, None

def process_api_event_stream(token, package_id, timestamp, device, arch, vc, sdk_val_for_api, hl, verbose):
    global CURRENT_API_CONFIG
    api_name_display = get_api_display_name(verbose)
    data_payload = {"hl": hl, "package": package_id, "device": device, "arch": arch, "vc": vc, "device_id": "", "sdk": sdk_val_for_api, "timestamp": timestamp}
    encoded_data = base64.urlsafe_b64encode(json.dumps(data_payload, separators=(',', ':')).encode('utf-8')).decode('utf-8')
    params = {"token": token, "data": encoded_data}
    try:
        if verbose: print(f"[*] ({api_name_display}) GET {CURRENT_API_CONFIG['API_URL']} for {package_id} (vc:{vc}, sdk:{sdk_val_for_api})...")
        with requests.get(CURRENT_API_CONFIG['API_URL'], headers=CURRENT_API_CONFIG['HEADERS_API_GET'], params=params, stream=True, timeout=60) as response:
            response.raise_for_status()
            full_event_data, last_event_json = "", None
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        full_event_data += decoded_line[6:]
                        try:
                            event_json = json.loads(full_event_data)
                            last_event_json = event_json
                            if verbose: print(f"[*] Stream progress ({api_name_display}) for {package_id} (vc:{vc},sdk:{sdk_val_for_api}): {event_json.get('progress', '')}% - {event_json.get('status', '')}")
                            full_event_data = ""
                        except json.JSONDecodeError: pass
                    elif not decoded_line.strip(): full_event_data = ""
            return last_event_json
    except requests.exceptions.RequestException as e:
        print(f"[!] ({api_name_display}) Error during API GET /get for {package_id} (vc:{vc},sdk:{sdk_val_for_api}): {e}")
        return None

def check_app_availability(token, package_id, timestamp, device, arch, vc, sdk_val_for_api, hl, verbose_flag):
    api_name_display = get_api_display_name(verbose_flag)
    print(f"[*] Checking availability with {api_name_display} for package: {package_id} (Version Code: {vc if vc != '0' else 'Latest'}, SDK: {sdk_val_for_api})...")
    last_event_json = process_api_event_stream(token, package_id, timestamp, device, arch, vc, sdk_val_for_api, hl, verbose=verbose_flag) # Pass verbose_flag as verbose
    if last_event_json:
        html_content = last_event_json.get("html", "")
        status_msg, progress = last_event_json.get("status", "Unknown"), last_event_json.get("progress", 0)
        if progress == 100 and "App not found" not in html_content and html_content.strip() and "apk_files_list" in html_content:
            print(f"[+] App '{package_id}' (vc:{vc if vc != '0' else 'Latest'},sdk:{sdk_val_for_api}) appears available via {api_name_display}. Status: {status_msg}")
            soup = BeautifulSoup(html_content, 'html.parser'); app_title = soup.select_one('ul.apk_ad_info li._title a'); app_vn_html = soup.select_one('ul.apk_ad_info span._version')
            if app_title: print(f"    App Name: {app_title.text.strip()}")
            if app_vn_html: print(f"    Version Displayed: {app_vn_html.text.strip()}")
            return PROC_SUCCESS
        else:
            error_msg = BeautifulSoup(html_content, 'html.parser').get_text(sep=' ', strip=True) if html_content else status_msg
            print(f"[!] ({api_name_display}) App '{package_id}' (vc:{vc if vc != '0' else 'Latest'},sdk:{sdk_val_for_api}) NOT available/error. Status: {status_msg} (Prog: {progress}%). Msg: {error_msg}")
            return PROC_FAILED
    else:
        print(f"[!] ({api_name_display}) Failed to get API response for '{package_id}' (vc:{vc if vc != '0' else 'Latest'},sdk:{sdk_val_for_api}).")
        return PROC_FAILED

def get_download_info(token, package_id, timestamp, device, arch, version_code_for_request, sdk_val_for_api, hl, show_stream_details, verbose_url_display):
    vc_display = version_code_for_request if version_code_for_request != "0" else "Latest"
    api_name_display = get_api_display_name(show_stream_details or verbose_url_display)
    if show_stream_details:
        print(f"[*] Requesting download information with {api_name_display} for {package_id} (Version Code: {vc_display}, SDK: {sdk_val_for_api})...")
    else:
        print(f"[*] Requesting download information for {package_id} (Version Code: {vc_display}, SDK: {sdk_val_for_api})...")
    last_event_json = process_api_event_stream(token, package_id, timestamp, device, arch, version_code_for_request, sdk_val_for_api, hl, verbose=show_stream_details) # Pass show_stream_details as verbose
    if last_event_json:
        progress, status = last_event_json.get('progress', 0), last_event_json.get('status', 'Unknown')
        if show_stream_details : print(f"[*] Final API stream status ({api_name_display}) for {package_id} (vc:{vc_display},sdk:{sdk_val_for_api}): {progress}% - {status}")
        elif not show_stream_details and progress != 100 : print(f"[*] API stream status ({get_api_display_name(verbose_url_display) if verbose_url_display else ''}) for {package_id} (vc:{vc_display},sdk:{sdk_val_for_api}): {progress}% - {status}".replace(" () "," ").strip())
        html_content = last_event_json.get("html", "")
        if progress == 100 and "App not found" not in html_content and html_content.strip():
            return parse_html_for_links(html_content, package_id, verbose=verbose_url_display, extract_history_token=True)
        else:
            error_msg = BeautifulSoup(html_content, 'html.parser').get_text(sep=' ', strip=True) if html_content else status
            print(f"[!] ({get_api_display_name(verbose_url_display) if verbose_url_display else ''}) App processing failed/not found for {package_id} (vc:{vc_display},sdk:{sdk_val_for_api}). Message: '{error_msg}'".replace(" () "," ").strip())
            return None, None
    else:
        print(f"[!] ({get_api_display_name(verbose_url_display) if verbose_url_display else ''}) No valid JSON from event stream for {package_id} (vc:{vc_display},sdk:{sdk_val_for_api}).".replace(" () "," ").strip())
        return None, None

def parse_html_for_links(html_content, package_id_for_log="", verbose=False, extract_history_token=False):
    soup = BeautifulSoup(html_content, 'html.parser'); apk_items = soup.select('div.apk_files_list div.apk_files_item a[href]'); download_links = []; history_token = None
    context_log = f"for {package_id_for_log} " if package_id_for_log else ""
    if not apk_items:
        single_apk_link = soup.select_one('a[rel="nofollow"][href*=".apk"]')
        if single_apk_link:
            url = single_apk_link['href']; parsed_dl_url, dl_query_params = urlparse(url), parse_qs(urlparse(url).query)
            filename = dl_query_params.get('filename', [os.path.basename(parsed_dl_url.path)])[0]; name_part, ext_part = os.path.splitext(filename)
            if not ext_part or ext_part.lower() not in [".apk", ".xapk", ".apks"]: filename = name_part + ".apk"
            download_links.append({'url': url, 'filename': filename}); url_display = f" -> {url[:50]}..." if verbose else ""
            print(f"[+] Found single APK {context_log}: {filename}{url_display}")
    for item in apk_items:
        url = item['href']; parsed_dl_url, dl_query_params = urlparse(url), parse_qs(urlparse(url).query)
        filename_param = dl_query_params.get('filename', [None])[0]
        filename = filename_param if filename_param else (item.select_one('span.der_name').text.strip() if item.select_one('span.der_name') else os.path.basename(parsed_dl_url.path))
        name_part, ext_part = os.path.splitext(filename)
        if not ext_part or ext_part.lower() not in [".apk", ".xapk", ".apks"]: filename = name_part + ".apk"
        download_links.append({'url': url, 'filename': filename}); url_display = f" -> {url[:50]}..." if verbose else ""
        print(f"[+] Found file {context_log}: {filename}{url_display}")
    if extract_history_token:
        history_button = soup.select_one('button#listverbtn[onclick*="fetchVersions"]')
        if history_button:
            onclick_val = history_button.get('onclick', ''); match = re.search(r"fetchVersions\('([^']+)'", onclick_val)
            if match: history_token = match.group(1);
            if verbose and history_token: print(f"[*] Extracted history token: {history_token[:10]}...")
    return download_links if download_links else None, history_token

def list_available_versions(package_id, history_token_h, verbose_flag):
    global CURRENT_API_CONFIG
    api_name_display = get_api_display_name(verbose_flag)
    if not history_token_h: print(f"[!] No history token available for {package_id} to fetch versions."); return False
    payload = {"package": package_id, "sl": 1, "h": history_token_h}
    print(f"[*] Fetching available versions for {package_id} using {api_name_display}...")
    if verbose_flag: print(f"[*] POST {CURRENT_API_CONFIG['GET_VERSION_URL']} payload: {json.dumps(payload)}")
    try:
        response = requests.post(CURRENT_API_CONFIG['GET_VERSION_URL'], headers=CURRENT_API_CONFIG['HEADERS_GET_VERSION'], json=payload, timeout=30)
        response.raise_for_status(); data = response.json()
        if verbose_flag: print(f"[*] {CURRENT_API_CONFIG['GET_VERSION_URL']} response ({api_name_display}): {json.dumps(data)[:200]}...")
        if "ver_list" in data and data["ver_list"]:
            ver_list_str = data["ver_list"]
            try: versions = json.loads(ver_list_str)
            except json.JSONDecodeError: print(f"[!] ({api_name_display}) Failed to parse version list JSON for {package_id}.");
            if verbose_flag: print(f"    Raw ver_list string: {ver_list_str}"); return False
            if not versions: print(f"[+] ({api_name_display}) No older versions found for {package_id}."); return True
            print(f"\n--- Available versions for {data.get('app_name', package_id)} (Package: {package_id}) ---")
            print(f"{'Version Code':<15} | {'Version Name':<20} | {'Update Time':<20} | {'Size (MB)':<10}"); print("-" * 75)
            sorted_vcs = sorted(versions.keys(), key=lambda x: int(x) if x.isdigit() else 0, reverse=True)
            for vc_str_key in sorted_vcs:
                ver_info = versions[vc_str_key]; vn = ver_info.get("versionName", "N/A"); ts_ms = ver_info.get("updateTime")
                ts_str = datetime.fromtimestamp(ts_ms / 1000).strftime('%Y-%m-%d %H:%M') if ts_ms else "N/A"
                size_b = ver_info.get("size"); size_mb = f"{int(size_b) / (1024*1024):.2f}" if isinstance(size_b, (int, float, str)) and str(size_b).isdigit() else "N/A"
                print(f"{vc_str_key:<15} | {vn:<20} | {ts_str:<20} | {size_mb:<10}")
            print("-" * 75); print(f"[*] To download a specific version, use: -dv VERSION_CODE (e.g., -dv {next(iter(sorted_vcs), 'VC_HERE')})")
            return True
        else: print(f"[!] ({api_name_display}) Could not retrieve version list. Response: {data.get('status', 'Unknown')}"); return False
    except requests.exceptions.RequestException as e: print(f"[!] ({api_name_display}) Error fetching versions for {package_id}: {e}"); return False
    except json.JSONDecodeError:
        print(f"[!] ({api_name_display}) Failed to decode JSON response for versions of {package_id}.")
        if verbose_flag and 'response' in locals(): print(f"    Raw response text: {response.text}"); return False

def download_file(url, directory, filename, package_id_for_log="", verbose=False):
    os.makedirs(directory, exist_ok=True); filepath = os.path.join(directory, filename)
    context_log = f"for {package_id_for_log} " if package_id_for_log else ""; url_display = f" from {url[:60]}..." if verbose else ""
    try:
        print(f"[*] Downloading {context_log}: {filename}{url_display}"); dl_headers = {"User-Agent": NEW_HEADERS_API_GET["User-Agent"]}
        response = requests.get(url, stream=True, headers=dl_headers, timeout=600); response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        with open(filepath, 'wb') as f, tqdm(desc=filename, total=total_size, unit='iB', unit_scale=True, unit_divisor=1024, leave=False) as bar:
            for chunk in response.iter_content(chunk_size=8192): size = f.write(chunk); bar.update(size)
        print(f"[+] Successfully downloaded {context_log}: {filepath}"); return filepath
    except requests.exceptions.RequestException as e: print(f"[!] Error downloading {filename} {context_log}: {e}")
    except Exception as e: print(f"[!] Unexpected error downloading {filename} {context_log}: {e}")
    if os.path.exists(filepath): os.remove(filepath)
    return None

def create_archive(apk_filepaths, output_directory, archive_base_name, archive_format="apks", app_version="unknown"):
    if not apk_filepaths:
        print(f"[!] No APKs for {archive_base_name} to archive.")
        return None

    archive_filename = f"{archive_base_name}.{archive_format}"
    archive_filepath = os.path.join(output_directory, archive_filename)
    
    original_package_id = archive_base_name.split('_vc')[0]
    base_apk_path = None

    try:
        if apk_filepaths:
            package_name_no_version = re.sub(r'_v[\d.]+$', '', original_package_id)
            sorted_apks = sorted(apk_filepaths, key=lambda p: os.path.getsize(p) if os.path.exists(p) else 0, reverse=True)
            if sorted_apks: base_apk_path = sorted_apks[0]
            for apk_p in apk_filepaths:
                name_lower = os.path.basename(apk_p).lower()
                if "base.apk" in name_lower or (package_name_no_version in name_lower and not any(x in name_lower for x in ["config.", "split_"])):
                    base_apk_path = apk_p; break
            if not base_apk_path and apk_filepaths: base_apk_path = apk_filepaths[0]
        
        print(f"[*] Creating .{archive_format} archive: {archive_filepath}")
        with zipfile.ZipFile(archive_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            for apk_path in apk_filepaths:
                if os.path.exists(apk_path): zf.write(apk_path, os.path.basename(apk_path)); print(f"  [+] Added: {os.path.basename(apk_path)}")
                else: print(f"  [!] Warning: File not found for archive: {apk_path}")
            if archive_format == "xapk":
                print(f"[*] Adding manifest.json for XAPK ({archive_base_name})..."); vc, vn = 0, app_version
                original_package_id_for_manifest = archive_base_name.split('_vc')[0]
                if base_apk_path:
                    match = re.search(r'(?:_v)?([\d.]+)\.(apk|xapk|apks)', os.path.basename(base_apk_path), re.IGNORECASE)
                    if match:
                        vn = match.group(1)
                        try:
                            parts = vn.split('.'); vc_str = "".join(filter(str.isdigit, parts[0]))
                            if len(parts) > 1: vc_str += "".join(filter(str.isdigit, parts[1]))[:2]
                            if len(parts) > 2: vc_str += "".join(filter(str.isdigit, parts[2]))[:2]
                            vc = int(vc_str) if vc_str else 0
                        except ValueError: pass
                manifest = {"package_name": original_package_id_for_manifest, "name": original_package_id_for_manifest, "version_code": vc, "version_name": vn,
                            "split_apks": [], "apk_path": os.path.basename(base_apk_path) if base_apk_path else None}
                for apk_path in apk_filepaths:
                    name = os.path.basename(apk_path);
                    if base_apk_path and apk_path == base_apk_path: continue
                    # Use original_package_id (without _vc) for cleaning split_id from package name
                    split_id = re.sub(r'_v[\d.]+$', '', os.path.splitext(name)[0]).replace(original_package_id, '').strip('._')
                    manifest["split_apks"].append({"file": name, "id": split_id if split_id else name})
                if len(apk_filepaths) == 1 and base_apk_path: manifest["split_apks"] = []
                zf.writestr("manifest.json", json.dumps(manifest, indent=2)); print("  [+] Added: manifest.json")
        print(f"[+] Successfully created .{archive_format} archive: {archive_filepath}"); print(f"[*] Install with a compatible installer (e.g., SAI)."); return archive_filepath
    except Exception as e:
        print(f"[!] Error creating archive for {archive_base_name}: {e}")

        if os.path.exists(archive_filepath):
            try:
                os.remove(archive_filepath)
                print(f"[*] Cleaned up partially created archive: {archive_filepath}")
            except Exception as e_rem:
                print(f"[!] Error cleaning up archive {archive_filepath}: {e_rem}")
        return None

def process_single_target(target_package_id, original_input_string, args_local): # Changed args to args_local
    global CURRENT_API_CONFIG
    package_id = target_package_id
    print(f"[*] Target Package ID: {package_id}")
    if original_input_string and original_input_string != package_id: print(f"    (From input: {original_input_string})")

    version_code_for_request = args_local.download_version if args_local.download_version else "0"
    sdk_version_arg_for_api = args_local.sdk_version

    base_package_output_dir = os.path.join(OUTPUT_BASE_DIR, package_id)
    app_output_dir = base_package_output_dir; archive_base_name = package_id
    if args_local.download_version:
        version_subfolder = f"vc{args_local.download_version}"; app_output_dir = os.path.join(base_package_output_dir, version_subfolder)
        archive_base_name = f"{package_id}_vc{args_local.download_version}"

    if args_local.check and not args_local.list_versions:
        token_check, timestamp_check, sdk_used = get_api_token(package_id, device=args_local.device, arch=args_local.arch, vc="0", sdk_version_arg=sdk_version_arg_for_api)
        if not token_check or not timestamp_check: return PROC_FAILED
        vc_to_check_with = args_local.download_version if args_local.download_version else "0"
        sdk_for_this_check, token_for_this_check, ts_for_this_check = sdk_used, token_check, timestamp_check
        if args_local.download_version and vc_to_check_with != "0":
             token_specific_vc, ts_specific_vc, sdk_specific_vc = get_api_token(package_id, device=args_local.device, arch=args_local.arch, vc=vc_to_check_with, sdk_version_arg=sdk_version_arg_for_api)
             if not token_specific_vc: print(f"[!] Could not get token for specific vc {vc_to_check_with} (sdk:{sdk_version_arg_for_api}) to check availability."); return PROC_FAILED
             sdk_for_this_check, token_for_this_check, ts_for_this_check = sdk_specific_vc, token_specific_vc, ts_specific_vc
        return check_app_availability(token_for_this_check, package_id, ts_for_this_check, args_local.device, args_local.arch, vc_to_check_with, sdk_for_this_check, "en", args_local.verbose)

    initial_token, initial_timestamp, initial_sdk_used = get_api_token(package_id, device=args_local.device, arch=args_local.arch, vc="0", sdk_version_arg=sdk_version_arg_for_api)
    if not initial_token or not initial_timestamp: print(f"[!] Could not retrieve initial API token for '{package_id}'."); return PROC_FAILED
    
    if args_local.list_versions:
        api_name_display_lv = get_api_display_name(args_local.verbose)
        print(f"[*] Fetching initial data (using SDK {initial_sdk_used} with {api_name_display_lv}) to find history token for {package_id}...")
        _, history_token = get_download_info(initial_token, package_id, initial_timestamp, args_local.device, args_local.arch, "0", initial_sdk_used, "en", 
                                             show_stream_details=args_local.verbose, verbose_url_display=args_local.verbose)
        if history_token: return PROC_SUCCESS if list_available_versions(package_id, history_token, verbose_flag=args_local.verbose) else PROC_FAILED
        else: print(f"[!] Could not find history token for {package_id}. Cannot list versions."); return PROC_FAILED

    token_to_use, timestamp_to_use, sdk_for_download = initial_token, initial_timestamp, initial_sdk_used
    effective_vc_for_download = "0"
    if args_local.download_version:
        effective_vc_for_download = args_local.download_version
        print(f"[*] Preparing to download specific version (vc: {effective_vc_for_download}) for {package_id}.")
        specific_vc_token, specific_vc_timestamp, specific_sdk_used = get_api_token(package_id, device=args_local.device, arch=args_local.arch, vc=effective_vc_for_download, sdk_version_arg=sdk_version_arg_for_api)
        if not specific_vc_token or not specific_vc_timestamp: print(f"[!] Failed to get token for version code {effective_vc_for_download} (sdk:{sdk_version_arg_for_api}). Cannot proceed."); return PROC_FAILED
        token_to_use, timestamp_to_use, sdk_for_download = specific_vc_token, specific_vc_timestamp, specific_sdk_used
    
    if os.path.isdir(app_output_dir):
        existing_apks = glob.glob(os.path.join(app_output_dir, '*.apk'))
        if existing_apks:
            log_folder_ref = os.path.basename(app_output_dir) if args_local.download_version else package_id
            print(f"[!] APKs for '{log_folder_ref}' (package: {package_id}) seem to exist in '{app_output_dir}'.")
            if args_local.universal_format:
                print(f"[*] Attempting to archive existing files for '{log_folder_ref}' into .{args_local.universal_format}...")
                version_from_existing = "unknown";
                for apk_f in existing_apks:
                    m = re.search(r'_v([\d.]+)\.(apk|xapk|apks)', os.path.basename(apk_f), re.IGNORECASE)
                    if m:
                        version_from_existing = m.group(1)
                        break
                return PROC_SKIPPED_EXISTING if create_archive(existing_apks, app_output_dir, archive_base_name, args_local.universal_format, version_from_existing) else PROC_FAILED
            else: print(f"[*] To re-download, remove directory '{app_output_dir}' or use -uf to archive. Skipping."); return PROC_SKIPPED_EXISTING
    
    time.sleep(3)
    download_infos, _ = get_download_info(token_to_use, package_id, timestamp_to_use, args_local.device, args_local.arch, effective_vc_for_download, sdk_for_download, "en", 
                                          show_stream_details=args_local.verbose, verbose_url_display=args_local.verbose)
    if not download_infos: return PROC_FAILED
    
    version_from_filename = "unknown"
    for info in download_infos:
        m = re.search(r'_v([\d.]+)\.(apk|xapk|apks)', info['filename'], re.IGNORECASE)
        if m:
            version_from_filename = m.group(1)
            break
    if not os.path.exists(app_output_dir): os.makedirs(app_output_dir, exist_ok=True)
    print(f"[*] Preparing to download files for {package_id} (Target Version: {version_from_filename if version_from_filename != 'unknown' else ('vc'+effective_vc_for_download if effective_vc_for_download != '0' else 'Latest')}, SDK: {sdk_for_download}) to: {app_output_dir}")
    
    downloaded_paths, success_count = [], 0
    for info in download_infos:
        path = download_file(info['url'], app_output_dir, info['filename'], package_id, verbose=args_local.verbose)
        if path: success_count += 1; downloaded_paths.append(path)
    
    log_folder_ref_dl = os.path.basename(app_output_dir) if args_local.download_version else package_id
    if not (success_count > 0) : print(f"\n[!] Failed to download any files for {log_folder_ref_dl}."); return PROC_FAILED
    elif success_count < len(download_infos): print(f"\n[!] Downloaded {success_count}/{len(download_infos)} files for {log_folder_ref_dl}.")
    else: print(f"\n[+] All {success_count} files for {log_folder_ref_dl} downloaded!")
    
    if success_count > 0 and len(downloaded_paths) > 1 and not args_local.universal_format:
        print(f"\n[*] Tip for {log_folder_ref_dl}: Multiple APKs downloaded. Use -uf apks or -uf xapk to archive.")
    if args_local.universal_format and downloaded_paths:
        if not create_archive(downloaded_paths, app_output_dir, archive_base_name, args_local.universal_format, version_from_filename):
            print(f"[!] Archiving failed for {archive_base_name}, but downloads were successful.")
    return PROC_SUCCESS

def main():
    global args_global
    print(BANNER)
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION} - Downloads APKs/Split APKs.", formatter_class=argparse.RawTextHelpFormatter)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--url", help="Single Google Play Store URL")
    input_group.add_argument("-p", "--package", dest="package_id_arg", help="Direct package ID (e.g., com.example.app)")
    input_group.add_argument("-if", "--input-file", dest="input_file", help="Path to a text file containing Google Play URLs or package IDs (one per line)")
    
    action_group = parser.add_mutually_exclusive_group(required=False)
    action_group.add_argument("-lv", "--list-versions", action="store_true", help="List available versions for the app(s).")
    action_group.add_argument("-dv", "--download-version", dest="download_version", metavar="VERSION_CODE", help="Download a specific version by its Version Code.")
    
    parser.add_argument("--device", default="phone", help="Device type (Default: phone)")
    parser.add_argument("--arch", default="arm64-v8a", help="Architecture (Default: arm64-v8a)")
    parser.add_argument("--sdk", dest="sdk_version", type=int, default=None,
                        help=f"Target SDK version for API requests (e.g., 30). If not set, API's default is used (New API: {NEW_DEFAULT_SDK}, Old API: {OLD_DEFAULT_SDK}).")
    parser.add_argument("--api-preference", choices=['new', 'old'], default='new',
                        help="API preference: 'new' (mi9.com, default), 'old' (apk.ad). Fallback is attempted.")
    parser.add_argument("-uf", "--universal-format", dest="universal_format", choices=['apks', 'xapk'], default=None, help="Archive format")
    parser.add_argument("--check", action="store_true", help="Modifier: Only check app availability, no download.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
    parser.add_argument("--delay", type=int, default=11, help="Delay in seconds between processing URLs/packages in batch mode (Default: 11)")
    parser.add_argument("--version", action="version", version=f"{TOOL_NAME} v{TOOL_VERSION} (%(prog)s)")
    args_global = parser.parse_args()

    if args_global.list_versions and args_global.download_version: parser.error("-lv and -dv are mutually exclusive.")
    if args_global.list_versions and args_global.universal_format: print("[!] Warning: -uf is ignored when listing versions (-lv).")
    if args_global.check and args_global.list_versions: print("[!] Info: --check is redundant with -lv. Proceeding to list."); args_global.check = False
    
    targets_to_process = []
    if args_global.input_file:
        try:
            with open(args_global.input_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if PLAY_URL in line: pkg_id = extract_package_id(line)
                        elif re.match(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$", line, re.IGNORECASE): pkg_id = line
                        else: print(f"[!] Skipping unrecognized line in file (line {line_num}): {line}"); continue
                        if pkg_id: targets_to_process.append((pkg_id, line if PLAY_URL in line else f"{PLAY_URL}{pkg_id}"))
                        else: print(f"[!] Skipping invalid URL/package in file (line {line_num}): {line}")
            if not targets_to_process: print(f"[!] Input file '{args_global.input_file}' is empty/no valid targets."); return
            print(f"[*] Loaded {len(targets_to_process)} targets from '{args_global.input_file}'.")
        except FileNotFoundError: print(f"[!] Error: Input file not found: {args_global.input_file}"); return
        except Exception as e: print(f"[!] Error reading input file '{args_global.input_file}': {e}"); return
    elif args_global.url:
        pkg_id = extract_package_id(args_global.url);
        if pkg_id: targets_to_process.append((pkg_id, args_global.url))
        else: print(f"[!] Invalid Google Play Store URL: {args_global.url}"); return
    elif args_global.package_id_arg:
        if not re.match(r"^[a-z0-9_]+(\.[a-z0-9_]+)+$", args_global.package_id_arg, re.IGNORECASE):
            print(f"[!] Invalid package ID format: {args_global.package_id_arg}."); return
        targets_to_process.append((args_global.package_id_arg, f"{PLAY_URL}{args_global.package_id_arg}"))
    
    successful_ops, failed_ops, skipped_ops = 0, 0, 0; last_op_involved_network = True
    for i, (target_pkg_id, original_input_log_str) in enumerate(targets_to_process):
        if i > 0 and last_op_involved_network:
            print(f"[*] Waiting {args_global.delay} seconds before next target...")
            time.sleep(args_global.delay)
        print(f"\n--- Processing Target {i+1}/{len(targets_to_process)}: {original_input_log_str} ---")
        current_op_status = PROC_FAILED
        try:
            current_op_status = process_single_target(target_pkg_id, original_input_log_str, args_global) # Pass args_global
            if current_op_status == PROC_SUCCESS: successful_ops +=1; last_op_involved_network = True
            elif current_op_status == PROC_SKIPPED_EXISTING: skipped_ops +=1; last_op_involved_network = False
            else: failed_ops +=1; last_op_involved_network = True
        except Exception as e:
            print(f"[!!!] CRITICAL ERROR processing {original_input_log_str}: {e}")
            if args_global.verbose: import traceback; traceback.print_exc()
            failed_ops +=1; last_op_involved_network = True
    if len(targets_to_process) > 1:
        print("\n--- Batch Processing Summary ---")
        print(f"Total targets processed: {len(targets_to_process)}"); print(f"Successful operations: {successful_ops}")
        print(f"Skipped (existing/archived): {skipped_ops}"); print(f"Failed operations: {failed_ops}"); print("-" * 30)

if __name__ == "__main__":
    main()
