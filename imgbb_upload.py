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
    try:
        payload = {
            "key": IMGBB_API_KEY,
            "image": image_data,
        }
        if name:
            payload["name"] = name

        response = requests.post(IMGBB_UPLOAD_URL, data=payload, timeout=30)
        result = response.json()

        if response.status_code == 200 and result.get("success"):
            return {"success": True, "url": result["data"]["url"]}
        else:
            error_msg = result.get("error", {}).get("message", "Unknown error")
            return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": str(e)}
