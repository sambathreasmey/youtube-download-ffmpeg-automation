import os
import json
import subprocess
import requests
import sys

def main():
    # GitHub Action passes these via environment variables or arguments
    # Using environment variables is often cleaner in Actions
    url = os.getenv("YT_URL")
    callback_url = os.getenv("CALLBACK_URL")
    job_id = os.getenv("JOB_ID")

    if not all([url, callback_url, job_id]):
        print("Missing required environment variables.")
        sys.exit(1)

    print(f"Fetching metadata for: {url}")

    try:
        # 1. Run yt-dlp to get JSON metadata
        cmd = ["yt-dlp", "-j", url]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        video_data = json.loads(result.stdout)

        # 2. Extract and simplify formats
        formats = []
        for f in video_data.get("formats", []):
            formats.append({
                "format_id": f.get("format_id"),
                "resolution": f.get("resolution") or f.get("format_note") or "audio only",
                "ext": f.get("ext"),
                "filesize": f.get("filesize") or f.get("filesize_approx") or 0,
                "vcodec": f.get("vcodec", "none"),
                "acodec": f.get("acodec", "none"),
                "fps": f.get("fps")
            })

        # 3. Prepare payload
        payload = {
            "job_id": job_id,
            "status": "success",
            "title": video_data.get("title"),
            "duration": video_data.get("duration"),
            "formats": formats
        }

        # 4. POST to your webhook
        print(f"Sending data to {callback_url}...")
        resp = requests.post(callback_url, json=payload, timeout=30)
        resp.raise_for_status()
        print(f"Callback successful. Status: {resp.status_code}")

    except Exception as e:
        print(f"Error: {e}")
        # Notify webhook of failure
        error_payload = {"job_id": job_id, "status": "error", "message": str(e)}
        try:
            requests.post(callback_url, json=error_payload, timeout=10)
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
