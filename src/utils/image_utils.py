"""Image processing helpers."""

import hashlib
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


def load_image_from_bytes(data: bytes) -> np.ndarray | None:
    """Load image bytes into BGR numpy array suitable for OpenCV."""
    try:
        pil_image = Image.open(BytesIO(data))
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        rgb = np.array(pil_image)
        # PIL gives RGB, OpenCV expects BGR
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except (UnidentifiedImageError, OSError):
        return None


def hash_image_bytes(data: bytes) -> str:
    """SHA-256 hash of image bytes for cache key."""
    return hashlib.sha256(data).hexdigest()


def compute_blur_score(image: np.ndarray) -> float:
    """Variance of Laplacian. Higher means sharper."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def deskew_image(image: np.ndarray) -> np.ndarray:
    """Detect skew angle and rotate to deskew."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        return image

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.5:
        return image

    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        image, rotation_matrix, (w, h),
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def enhance_for_ocr(image: np.ndarray) -> np.ndarray:
    """Standard preprocessing pipeline before OCR."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Adaptive threshold for varying lighting
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )
    # Convert back to BGR for compatibility
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
