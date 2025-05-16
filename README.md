# PlayRetrieve

**By: Muhammad Khizer Javed (SecurityBreached.org)**  
*Website: [whoami.securitybreached.org](https://whoami.securitybreached.org/)*

PlayRetrieve is a command-line Python script that allows you to download Android application packages (APKs), including split APKs, directly using a Google Play Store URL. It interfaces with the API used by [apk.ad](https://apk.ad/) to fetch download links.

The tool can download individual APK files (latest or specific versions) and optionally package multiple split APKs into a single `.apks` (APK Set) or `.xapk` archive for convenient installation. It also supports batch processing of URLs, app availability checks, and listing available app versions.

## Features

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
  ___ _           ___     _       _
 | _ \ |__ _ _  _| _ \___| |_ _ _(_)_____ _____
 |  _/ / _` | || |   / -_)  _| '_| / -_) V / -_)
 |_| |_\__,_|\_, |_|_\___|\__|_| |_\___|\_/\___|
             |__/
              PlayRetrieve v1.1
Muhammad Khizer Javed | whoami.securitybreached.org
----------------------------------------------------

usage: PlayRetrieve1.py [-h] (--url URL | -if INPUT_FILE) [-lv | -dv VERSION_CODE] [--device DEVICE] [--arch ARCH] [-uf {apks,xapk}] [--check] [-v] [--delay DELAY] [--version]

PlayRetrieve v1.1 - Downloads APKs/Split APKs.

options:
  -h, --help            show this help message and exit
  --url URL             Single Google Play Store URL
  -if, --input-file INPUT_FILE
                        Path to a text file containing Google Play URLs (one per line)
  -lv, --list-versions  List available versions for the app(s).
  -dv, --download-version VERSION_CODE
                        Download a specific version by its Version Code.
  --device DEVICE       Device type (Default: phone)
  --arch ARCH           Architecture (Default: arm64-v8a)
  -uf, --universal-format {apks,xapk}
                        Archive format
  --check               Modifier: Only check app availability (for latest or specified -dv), no download.
  -v, --verbose         Enable verbose output.
  --delay DELAY         Delay in seconds between processing URLs in batch mode (Default: 11)
  --version             show program's version number and exit
```

## Examples

**Download APKs for a single app:**  
```
python PlayRetrieve.py --url "https://play.google.com/store/apps/details?id=com.binance.dev"
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
