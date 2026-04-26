import os
import json
import requests
import sys
import yt_dlp

def main():
    # Fetch environment variables from GitHub Action
    url = os.getenv("YT_URL")
    callback_url = os.getenv("CALLBACK_URL")
    job_id = os.getenv("JOB_ID")

    if not all([url, callback_url, job_id]):
        print("Error: Missing required environment variables (YT_URL, CALLBACK_URL, JOB_ID).")
        sys.exit(1)

    # Configuration for yt-dlp
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        # Mimic a real browser to avoid 403/429 errors
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
    }

    print(f"Extracting metadata for: {url}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info without downloading
            info = ydl.extract_info(url, download=False)

            # Filter and simplify format data
            formats = []
            for f in info.get("formats", []):
                formats.append({
                    "format_id": f.get("format_id"),
                    "resolution": f.get("resolution") or f.get("format_note") or "audio only",
                    "ext": f.get("ext"),
                    "filesize": f.get("filesize") or f.get("filesize_approx") or 0,
                    "vcodec": f.get("vcodec", "none"),
                    "acodec": f.get("acodec", "none"),
                    "fps": f.get("fps")
                })

            # Build the success payload
            payload = {
                "job_id": job_id,
                "status": "success",
                "title": info.get("title"),
                "duration": info.get("duration"),
                "thumbnail": info.get("thumbnail"),
                "formats": formats
            }

        # Send to your webhook
        print(f"Sending metadata to callback: {callback_url}")
        resp = requests.post(callback_url, json=payload, timeout=30)
        resp.raise_for_status()
        print(f"Success! Status Code: {resp.status_code}")

    except Exception as e:
        print(f"Extraction failed: {str(e)}")
        # Optional: Notify your webhook about the failure
        error_payload = {"job_id": job_id, "status": "error", "message": str(e)}
        try:
            requests.post(callback_url, json=error_payload, timeout=10)
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
