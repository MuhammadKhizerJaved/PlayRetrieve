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

# By: SecurityBreached
# https://whoami.securitybreached.org/
# Muhammad Khizer Javed
# khizerjaved@securitybreached.org

TOKEN_URL = "https://token.apk.ad/"
API_URL = "https://api.apk.ad/get"
OUTPUT_BASE_DIR = "apk_downloads"
TOOL_NAME = "PlayRetrieve"
TOOL_VERSION = "1.0"
Author_Name = "Muhammad Khizer Javed"
Author_URL = "whoami.securitybreached.org"


HEADERS_TOKEN = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://apkdownloader.pages.dev/",
    "Content-Type": "application/json",
    "Origin": "https://apkdownloader.pages.dev",
    "Connection": "keep-alive"
}

HEADERS_API = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Accept": "text/event-stream",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://apkdownloader.pages.dev/",
    "Origin": "https://apkdownloader.pages.dev",
    "Connection": "keep-alive"
}

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


def extract_package_id(play_store_url):
    if not play_store_url or not play_store_url.startswith("https://play.google.com/store/apps/details?id="):
        return None
    parsed_url = urlparse(play_store_url)
    if parsed_url.netloc not in ["play.google.com", "www.play.google.com"]:
        return None
    query_params = parse_qs(parsed_url.query)
    return query_params.get('id', [None])[0]

def get_api_token(package_id, device="phone", arch="arm64-v8a", vc="0", sdk="default"):
    payload = {
        "package": package_id, "device": device, "arch": arch,
        "vc": vc, "device_id": "", "sdk": sdk
    }
    try:
        response = requests.post(TOKEN_URL, headers=HEADERS_TOKEN, json=payload, timeout=30)
        try: data = response.json()
        except json.JSONDecodeError as e:
            print(f"[!!!] FAILED TO DECODE JSON (TOKEN) for {package_id} (Error: {e}). Status: {response.status_code}\nText: {response.text}")
            return None, None
        response.raise_for_status()
        return (data.get("token"), data.get("timestamp")) if data.get("success") else (
            print(f"[!] Failed to get token for {package_id} (API success:false): {data.get('message', data)}"), None, None)[1:]
    except requests.exceptions.RequestException as e:
        print(f"[!] Error requesting token for {package_id}: {e}")
        return None, None

def process_api_event_stream(token, package_id, timestamp, device="phone", arch="arm64-v8a", vc="0", sdk="default", hl="en", verbose=False):
    data_payload = {
        "hl": hl, "package": package_id, "device": device, "arch": arch,
        "vc": vc, "device_id": "", "sdk": sdk, "timestamp": timestamp
    }
    encoded_data = base64.urlsafe_b64encode(json.dumps(data_payload, separators=(',', ':')).encode('utf-8')).decode('utf-8')
    params = {"token": token, "data": encoded_data}
    try:
        with requests.get(API_URL, headers=HEADERS_API, params=params, stream=True, timeout=60) as response:
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
                            if verbose: print(f"[*] Stream progress for {package_id}: {event_json.get('progress', '')}% - {event_json.get('status', '')}")
                            full_event_data = ""
                        except json.JSONDecodeError: pass
                    elif not decoded_line.strip(): full_event_data = ""
            return last_event_json
    except requests.exceptions.RequestException as e:
        print(f"[!] Error during API request for {package_id}: {e}")
        return None

def check_app_availability(token, package_id, timestamp, device="phone", arch="arm64-v8a", vc="0", sdk="default", hl="en", verbose=False):
    print(f"[*] Checking availability for package: {package_id}...")
    last_event_json = process_api_event_stream(token, package_id, timestamp, device, arch, vc, sdk, hl, verbose=verbose)
    if last_event_json:
        html_content = last_event_json.get("html", "")
        status_msg, progress = last_event_json.get("status", "Unknown"), last_event_json.get("progress", 0)
        if progress == 100 and "App not found" not in html_content and html_content.strip() and "apk_files_list" in html_content:
            print(f"[+] App '{package_id}' appears to be available for download. Status: {status_msg}")
            soup = BeautifulSoup(html_content, 'html.parser')
            app_title = soup.select_one('ul.apk_ad_info li._title a')
            app_version = soup.select_one('ul.apk_ad_info span._version')
            if app_title: print(f"    App Name: {app_title.text.strip()}")
            if app_version: print(f"    Version: {app_version.text.strip()}")
            return PROC_SUCCESS 
        else:
            error_msg = BeautifulSoup(html_content, 'html.parser').get_text(sep=' ', strip=True) if html_content else status_msg
            print(f"[!] App '{package_id}' NOT available/error. Status: {status_msg} (Prog: {progress}%). Msg: {error_msg}")
            return PROC_FAILED 
    else:
        print(f"[!] Failed to get API response for '{package_id}'.")
        return PROC_FAILED 

def get_download_info(token, package_id, timestamp, device="phone", arch="arm64-v8a", vc="0", sdk="default", hl="en", show_stream_details=False, verbose_url_display=False):
    print(f"[*] Requesting download information for {package_id}...")
    last_event_json = process_api_event_stream(token, package_id, timestamp, device, arch, vc, sdk, hl, verbose=show_stream_details)
    if last_event_json:
        progress, status = last_event_json.get('progress', 0), last_event_json.get('status', 'Unknown')
        if show_stream_details : print(f"[*] Final API stream status for {package_id}: {progress}% - {status}")
        elif not show_stream_details and progress != 100 :
            print(f"[*] API stream status for {package_id}: {progress}% - {status}")
        html_content = last_event_json.get("html", "")
        if progress == 100 and "App not found" not in html_content and html_content.strip():
            return parse_html_for_links(html_content, package_id, verbose=verbose_url_display)
        else:
            error_msg = BeautifulSoup(html_content, 'html.parser').get_text(sep=' ', strip=True) if html_content else status
            print(f"[!] App processing failed/not found for {package_id}. Message: '{error_msg}'")
            return None
    else:
        print(f"[!] No valid JSON from event stream for {package_id}.")
        return None

def parse_html_for_links(html_content, package_id_for_log="", verbose=False):
    soup = BeautifulSoup(html_content, 'html.parser')
    apk_items = soup.select('div.apk_files_list div.apk_files_item a[href]')
    download_links = []
    context_log = f"for {package_id_for_log} " if package_id_for_log else ""
    if not apk_items:
        single_apk_link = soup.select_one('a[rel="nofollow"][href*=".apk"]')
        if single_apk_link:
            url = single_apk_link['href']
            parsed_dl_url, dl_query_params = urlparse(url), parse_qs(urlparse(url).query)
            filename = dl_query_params.get('filename', [os.path.basename(parsed_dl_url.path)])[0]
            name_part, ext_part = os.path.splitext(filename)
            if not ext_part or ext_part.lower() not in [".apk", ".xapk", ".apks"]: filename = name_part + ".apk"
            download_links.append({'url': url, 'filename': filename})
            url_display = f" -> {url[:50]}..." if verbose else ""
            print(f"[+] Found single APK {context_log}: {filename}{url_display}")
    for item in apk_items:
        url = item['href']
        parsed_dl_url, dl_query_params = urlparse(url), parse_qs(urlparse(url).query)
        filename_param = dl_query_params.get('filename', [None])[0]
        filename = filename_param if filename_param else (item.select_one('span.der_name').text.strip() if item.select_one('span.der_name') else os.path.basename(parsed_dl_url.path))
        name_part, ext_part = os.path.splitext(filename)
        if not ext_part or ext_part.lower() not in [".apk", ".xapk", ".apks"]: filename = name_part + ".apk"
        download_links.append({'url': url, 'filename': filename})
        url_display = f" -> {url[:50]}..." if verbose else ""
        print(f"[+] Found file {context_log}: {filename}{url_display}")
    return download_links if download_links else None

def download_file(url, directory, filename, package_id_for_log="", verbose=False):
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    context_log = f"for {package_id_for_log} " if package_id_for_log else ""
    url_display = f" from {url[:60]}..." if verbose else ""
    try:
        print(f"[*] Downloading {context_log}: {filename}{url_display}")
        dl_headers = {"User-Agent": HEADERS_API["User-Agent"]}
        response = requests.get(url, stream=True, headers=dl_headers, timeout=600)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        with open(filepath, 'wb') as f, tqdm(desc=filename, total=total_size, unit='iB', unit_scale=True, unit_divisor=1024, leave=False) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                size = f.write(chunk)
                bar.update(size)
        print(f"[+] Successfully downloaded {context_log}: {filepath}")
        return filepath
    except requests.exceptions.RequestException as e:
        print(f"[!] Error downloading {filename} {context_log}: {e}")
    except Exception as e:
        print(f"[!] Unexpected error downloading {filename} {context_log}: {e}")
    if os.path.exists(filepath): os.remove(filepath)
    return None

def create_archive(apk_filepaths, output_directory, package_name, archive_format="apks", app_version="unknown"):
    if not apk_filepaths: print(f"[!] No APKs for {package_name} to archive."); return None
    archive_filename, archive_filepath = f"{package_name}.{archive_format}", os.path.join(output_directory, f"{package_name}.{archive_format}")
    base_apk_path = None
    if apk_filepaths:
        package_name_no_version = re.sub(r'_v[\d.]+$', '', package_name)
        sorted_apks = sorted(apk_filepaths, key=lambda p: os.path.getsize(p) if os.path.exists(p) else 0, reverse=True)
        if sorted_apks: base_apk_path = sorted_apks[0]
        for apk_p in apk_filepaths:
            name_lower = os.path.basename(apk_p).lower()
            if "base.apk" in name_lower or (package_name_no_version in name_lower and not any(x in name_lower for x in ["config.", "split_"])):
                base_apk_path = apk_p; break
        if not base_apk_path and apk_filepaths: base_apk_path = apk_filepaths[0]
    try:
        print(f"[*] Creating .{archive_format} archive for {package_name}: {archive_filepath}")
        with zipfile.ZipFile(archive_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
            for apk_path in apk_filepaths:
                if os.path.exists(apk_path): zf.write(apk_path, os.path.basename(apk_path)); print(f"  [+] Added: {os.path.basename(apk_path)}")
                else: print(f"  [!] Warning: File not found for archive: {apk_path}")
            if archive_format == "xapk":
                print(f"[*] Adding manifest.json for XAPK ({package_name})...")
                vc, vn = 0, app_version
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
                manifest = {"package_name": package_name, "name": package_name, "version_code": vc, "version_name": vn,
                            "split_apks": [], "apk_path": os.path.basename(base_apk_path) if base_apk_path else None}
                for apk_path in apk_filepaths:
                    name = os.path.basename(apk_path)
                    if base_apk_path and apk_path == base_apk_path: continue
                    split_id = re.sub(r'_v[\d.]+$', '', os.path.splitext(name)[0]).replace(package_name_no_version, '').strip('._')
                    manifest["split_apks"].append({"file": name, "id": split_id if split_id else name})
                if len(apk_filepaths) == 1 and base_apk_path: manifest["split_apks"] = []
                zf.writestr("manifest.json", json.dumps(manifest, indent=2)); print("  [+] Added: manifest.json")
        print(f"[+] Successfully created .{archive_format} archive for {package_name}: {archive_filepath}")
        print(f"[*] Install with a compatible installer (e.g., SAI).")
        return archive_filepath
    except Exception as e: print(f"[!] Error creating archive for {package_name}: {e}")
    if os.path.exists(archive_filepath): os.remove(archive_filepath)
    return None

def process_single_url(play_url, args):
    package_id = extract_package_id(play_url)
    if not package_id:
        print(f"[!] Invalid Google Play Store URL or no package ID found: {play_url}")
        return PROC_FAILED

    print(f"[*] Target Package ID: {package_id}")

    if args.check:
        token, timestamp = get_api_token(package_id, device=args.device, arch=args.arch)
        if not token or not timestamp: return PROC_FAILED
        # check_app_availability already returns PROC_SUCCESS or PROC_FAILED
        return check_app_availability(token, package_id, timestamp, device=args.device, arch=args.arch, verbose=args.verbose)

    app_output_dir = os.path.join(OUTPUT_BASE_DIR, package_id)
    if os.path.isdir(app_output_dir):
        existing_apks = glob.glob(os.path.join(app_output_dir, '*.apk'))
        if existing_apks:
            print(f"[!] APKs for '{package_id}' seem to exist in '{app_output_dir}'.")
            if args.universal_format:
                print(f"[*] Attempting to archive existing files for '{package_id}' into .{args.universal_format}...")
                version = "unknown"
                for apk_f in existing_apks:
                    m = re.search(r'_v([\d.]+)\.(apk|xapk|apks)', os.path.basename(apk_f), re.IGNORECASE)
                    if m: version = m.group(1); break
                if create_archive(existing_apks, app_output_dir, package_id, args.universal_format, version):
                    return PROC_SKIPPED_EXISTING # Archived existing, no major network op for download
                else:
                    return PROC_FAILED # Archiving failed
            else:
                print(f"[*] To re-download, remove directory or use -uf to archive existing. Skipping '{package_id}'.")
                return PROC_SKIPPED_EXISTING # Skipped due to existing files
    
    token, timestamp = get_api_token(package_id, device=args.device, arch=args.arch)
    if not token or not timestamp: return PROC_FAILED
    print(f"[+] Token for {package_id}: {token[:10]}...")
    time.sleep(2) # Short delay after token fetch

    download_infos = get_download_info(token, package_id, timestamp, device=args.device, arch=args.arch,
                                       show_stream_details=args.verbose, verbose_url_display=args.verbose)
    if not download_infos: return PROC_FAILED

    version = "unknown"
    for info in download_infos:
        m = re.search(r'_v([\d.]+)\.(apk|xapk|apks)', info['filename'], re.IGNORECASE)
        if m: version = m.group(1); break
    
    if not os.path.exists(app_output_dir): os.makedirs(app_output_dir, exist_ok=True)
    print(f"[*] Preparing to download files for {package_id} to: {app_output_dir}")

    downloaded_paths, success_count = [], 0
    for info in download_infos:
        path = download_file(info['url'], app_output_dir, info['filename'], package_id, verbose=args.verbose)
        if path: success_count += 1; downloaded_paths.append(path)
    
    if not (success_count > 0) : # If no files downloaded at all
        print(f"\n[!] Failed to download any files for {package_id}.")
        return PROC_FAILED
    elif success_count < len(download_infos): # Partial success
        print(f"\n[!] Downloaded {success_count}/{len(download_infos)} files for {package_id}.")
    else: # All files downloaded
         print(f"\n[+] All {success_count} files for {package_id} downloaded!")


    if success_count > 0 and len(downloaded_paths) > 1 and not args.universal_format:
        print(f"\n[*] Tip for {package_id}: Multiple APKs downloaded. Use -uf apks or -uf xapk to archive.")
    
    if args.universal_format and downloaded_paths:
        if not create_archive(downloaded_paths, app_output_dir, package_id, args.universal_format, version):
            # If archiving fails after successful download, still count download as a success for summary
            print(f"[!] Archiving failed for {package_id}, but downloads were successful.")
    
    return PROC_SUCCESS # At least one file was downloaded

def main():
    print(BANNER)
    parser = argparse.ArgumentParser(
        description=f"{TOOL_NAME} v{TOOL_VERSION} - Downloads APKs/Split APKs.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Single Google Play Store URL")
    group.add_argument("-if", "--input-file", dest="input_file", help="Path to a text file containing Google Play URLs (one per line)")

    parser.add_argument("--device", default="phone", help="Device type (Default: phone)")
    parser.add_argument("--arch", default="arm64-v8a", help="Architecture (Default: arm64-v8a)")
    parser.add_argument("-uf", "--universal-format", dest="universal_format", choices=['apks', 'xapk'], default=None, help="Archive format")
    parser.add_argument("--check", action="store_true", help="Only check app availability, no download")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
    parser.add_argument("--delay", type=int, default=11, help="Delay in seconds between processing URLs in batch mode (Default: 5)") # New delay argument
    parser.add_argument("--version", action="version", version=f"{TOOL_NAME} v{TOOL_VERSION} (%(prog)s)")
    args = parser.parse_args()

    urls_to_process = []
    if args.input_file:
        try:
            with open(args.input_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'): urls_to_process.append(line)
            if not urls_to_process: print(f"[!] Input file '{args.input_file}' is empty/no valid URLs."); return
            print(f"[*] Loaded {len(urls_to_process)} URLs from '{args.input_file}'.")
        except FileNotFoundError: print(f"[!] Error: Input file not found: {args.input_file}"); return
        except Exception as e: print(f"[!] Error reading input file '{args.input_file}': {e}"); return
    elif args.url:
        urls_to_process.append(args.url)
    
    successful_ops, failed_ops, skipped_ops = 0, 0, 0
    last_op_involved_network = True # Assume first op might involve network

    for i, play_url in enumerate(urls_to_process):
        # Apply delay only if the PREVIOUS operation involved network calls
        # and this is not the very first URL.
        if i > 0 and last_op_involved_network:
            print(f"[*] Waiting {args.delay} seconds before next URL to be polite to the API...")
            time.sleep(args.delay)

        print(f"\n--- Processing URL {i+1}/{len(urls_to_process)}: {play_url} ---")
        current_op_status = PROC_FAILED # Default to failed
        try:
            current_op_status = process_single_url(play_url, args)
            if current_op_status == PROC_SUCCESS:
                successful_ops +=1
                last_op_involved_network = True # API was hit for download/check
            elif current_op_status == PROC_SKIPPED_EXISTING:
                skipped_ops +=1
                last_op_involved_network = False # API was not hit for download info
            else: # PROC_FAILED
                failed_ops +=1
                last_op_involved_network = True # Assume failure might have involved an API attempt
        except Exception as e:
            print(f"[!!!] CRITICAL ERROR processing {play_url}: {e}")
            failed_ops +=1
            last_op_involved_network = True # Assume failure implies network attempt

    if len(urls_to_process) > 1:
        print("\n--- Batch Processing Summary ---")
        print(f"Total URLs processed: {len(urls_to_process)}")
        print(f"Successful operations: {successful_ops}")
        print(f"Skipped (already existing/archived): {skipped_ops}")
        print(f"Failed operations: {failed_ops}")
        print("------------------------------")

if __name__ == "__main__":
    main()