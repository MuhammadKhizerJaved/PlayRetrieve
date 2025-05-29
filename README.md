# PlayRetrieve

**By: Muhammad Khizer Javed (SecurityBreached.org)**  
*Website: [whoami.securitybreached.org](https://whoami.securitybreached.org/)*

PlayRetrieve is a command-line Python script that allows you to download Android application packages (APKs, XAPKs, Split APKs), including specific historical versions, directly using Google Play Store URLs or package IDs. It now robustly interfaces with the API used by **mi9.com** (derived from the previous apkdownloader.pages.dev service) to fetch download links.

The tool can download individual files (latest or specific versions) and optionally package multiple split APKs into a single `.apks` (APK Set) or `.xapk` archive. It supports batch processing, app availability checks, and listing available app versions.

## Features

# **Reliable Downloads:** Uses the current mi9 API for fetching all app types, including `.xapk` and `.zip` files
* Download latest or specific versions of APKs/Split APKs using a Google Play Store URL.
* List available historical versions of an app (with version codes, names, update times, and sizes).
* Download a specific app version using its **Version Code**.
* Batch processing of multiple URLs from a text file.
* Optionally package downloaded split APKs into:
  * `.apks` (APK Set archive)
  * `.xapk` (includes a basic `manifest.json`)
* Configurable device type and CPU architecture for fetching specific APK variants.
* Delay support (`--delay`) in batch processing mode to avoid rate-limiting.

## Usage

```
python PlayRetrieve.py [ARGUMENT_GROUP] [OPTIONS]
```

## Help

```
python PlayRetrieve.py --help


  ___ _           ___     _       _
 | _ \ |__ _ _  _| _ \___| |_ _ _(_)_____ _____
 |  _/ / _` | || |   / -_)  _| '_| / -_) V / -_)
 |_| |_\__,_|\_, |_|_\___|\__|_| |_\___|\_/\___|
             |__/
              PlayRetrieve v1.7.1
Muhammad Khizer Javed | whoami.securitybreached.org
----------------------------------------------------

usage: PlayRetrieve2.py [-h] (--url URL | -p PACKAGE_ID_ARG | -if INPUT_FILE) [-lv | -dv VERSION_CODE] [--device DEVICE] [--arch ARCH] [--sdk SDK_VERSION] [-uf {apks,xapk}] [--check]
                        [-v] [--delay DELAY] [--version]

PlayRetrieve v1.7.1 - Downloads APKs/Split APKs.

options:
  -h, --help            show this help message and exit
  --url URL             Single Google Play Store URL
  -p, --package PACKAGE_ID_ARG
                        Direct package ID (e.g., com.example.app)
  -if, --input-file INPUT_FILE
                        Path to a text file containing Google Play URLs or package IDs (one per line)
  -lv, --list-versions  List available versions for the app(s).
  -dv, --download-version VERSION_CODE
                        Download a specific version by its Version Code.
  --device DEVICE       Device type (Default: phone)
  --arch ARCH           Architecture (Default: arm64-v8a)
  --sdk SDK_VERSION     Target SDK version for API requests (e.g., 30). If not set, API's default is used (Current API default: 30).
  -uf, --universal-format {apks,xapk}
                        Archive format
  --check               Modifier: Only check app availability, no download.
  -v, --verbose         Enable verbose output.
  --delay DELAY         Delay in seconds between processing URLs/packages in batch mode (Default: 9)
  --version             show program's version number and exit
```

## Examples

**Download APKs for a single app:**  
```
python PlayRetrieve.py --url "https://play.google.com/store/apps/details?id=com.binance.dev"
```

**Download APKs for a single app by Package Name:**  
```
python PlayRetrieve.py --package com.binance.dev
```

**List available versions for an app:**  
```
python PlayRetrieve.py --url "https://play.google.com/store/apps/details?id=com.binance.dev -lv"
```

**Download a specific version of an app using its Version Code (e.g., VC 123):**  
```
python PlayRetrieve.py --url "https://play.google.com/store/apps/details?id=com.binance.dev" -dv 123
```

**Download and create an .apks archive:**  
```
python PlayRetrieve.py --url "https://play.google.com/store/apps/details?id=com.google.android.youtube" -uf apks
```

**Download and create an .xapk archive with custom architecture:**  
```
python PlayRetrieve.py --url "YOUR_APP_URL" --arch armeabi-v7a -uf xapk
```

**Batch processing from a file:**  
Create `my_apps.txt` with:
```
https://play.google.com/store/apps/details?id=com.twitter.android
https://play.google.com/store/apps/details?id=com.whatsapp
com.zong.customercare
```

Then run:  
```
python PlayRetrieve.py --input-file my_apps.txt
```

**Use previously downloaded APKs to create an archive:**  
```
python PlayRetrieve.py --url "https://play.google.com/store/apps/details?id=com.binance.dev" -uf xapk
```

### Options:

**Devices:**
```
tv
tablet
watch
phone
```

**Architecture:**
```
arm64-v8a
armeabi-v7a
x86
x86_64
```

## Batch Processing Delay

By default, if the user doesn't specify the `--delay` argument, it's set to **11 seconds**.

### Demo

![https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/help.png](https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/help.png)

![https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/down_single_url.png](https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/down_single_url.png)

![https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/List-Versions.png](https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/List-Versions.png)

![https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/Download-Specific-Version.png](https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/Download-Specific-Version.png)

![https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/download_multiple_apps.png](https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/download_multiple_apps.png)

![https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/archieve_apps.png](https://raw.githubusercontent.com/MuhammadKhizerJaved/PlayRetrieve/refs/heads/main/images/archieve_apps.png)

## Disclaimer

This tool depends on a third-party API. If the API changes, breaks, or becomes unavailable, the script may fail. Use it responsibly.

## License

This project is licensed under the MIT License.
