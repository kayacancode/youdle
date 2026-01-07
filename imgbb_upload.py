# imgbb_upload.py
# Upload images to imgBB API

import requests
import os

IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"

# Default image for RECALL articles (no generated image)
DEFAULT_RECALL_IMAGE_URL = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgex6VD3Nxp8182Dnvc09taqAndjcsVSahJc0hFQIct8Sk0oHMoQIJX8WjAsT_ruo_CS389jWfmMCLqe8HPLZbkU2pTbXp_UUwx02tJp19wegZB97c0DztKHFHtl9_JvbBvlTIQ3CdEurOMtjh1mNHkwF6-u_a39cJnyTFHY1q08cXQh6WOcHm6r28rUiMP/w558-h371/IMG_0682.jpg"


def upload_image_to_imgbb(image_data: str, name: str = None) -> dict:
    """
    Upload base64 image data to imgBB.

    Args:
        image_data: Base64 encoded image string
        name: Optional image name

    Returns:
        {"success": True, "url": "https://i.ibb.co/..."} or {"success": False, "error": "..."}
    """
    print(f"[imgBB] Starting upload for: {name}", flush=True)
    print(f"[imgBB] API key present: {bool(IMGBB_API_KEY)}", flush=True)
    print(f"[imgBB] Image data length: {len(image_data) if image_data else 0} chars", flush=True)

    if not IMGBB_API_KEY:
        print("[imgBB] ✗ No API key configured!", flush=True)
        return {"success": False, "error": "IMGBB_API_KEY not configured"}

    try:
        payload = {
            "key": IMGBB_API_KEY,
            "image": image_data,
        }
        if name:
            payload["name"] = name

        response = requests.post(IMGBB_UPLOAD_URL, data=payload, timeout=30)
        print(f"[imgBB] Response status: {response.status_code}", flush=True)
        result = response.json()

        if response.status_code == 200 and result.get("success"):
            url = result["data"]["url"]
            print(f"[imgBB] ✓ Upload successful: {url}", flush=True)
            return {"success": True, "url": url}
        else:
            error_msg = result.get("error", {}).get("message", "Unknown error")
            print(f"[imgBB] ✗ Upload failed: {error_msg}", flush=True)
            return {"success": False, "error": error_msg}
    except Exception as e:
        print(f"[imgBB] ✗ Exception: {str(e)}", flush=True)
        return {"success": False, "error": str(e)}
