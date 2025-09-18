"""
Utilities to build and load a precomputed gallery face index.

The index stores, for each image in the gallery:
- image filename
- list of face encodings
- list of corresponding face locations

This allows matching to skip per-request gallery face detection and encoding.
"""

import os
import pickle
from typing import Dict, List, Tuple, Any

import cv2
import face_recognition


def build_gallery_index(gallery_folder: str, index_path: str) -> Dict[str, Any]:
    """
    Scan the gallery and compute face encodings and locations for each image.

    Returns a dict mapping filename -> {"encodings": [...], "locations": [...]} and
    persists it to index_path via pickle.
    """
    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    ALLOWED_EXTS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
    index: Dict[str, Dict[str, List]] = {}

    if not os.path.isdir(gallery_folder):
        # Persist an empty index
        with open(index_path, 'wb') as f:
            pickle.dump(index, f)
        return index

    for filename in os.listdir(gallery_folder):
        if not filename.lower().endswith(ALLOWED_EXTS):
            continue

        path = os.path.join(gallery_folder, filename)
        img_bgr = cv2.imread(path)
        if img_bgr is None:
            continue

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(img_rgb)
        face_encodings = face_recognition.face_encodings(img_rgb, face_locations)

        index[filename] = {
            "encodings": face_encodings,
            "locations": face_locations,
        }

    with open(index_path, 'wb') as f:
        pickle.dump(index, f)

    return index


def load_gallery_index(index_path: str) -> Dict[str, Dict[str, List]]:
    """Load the gallery index from disk if present; otherwise return empty dict."""
    if not os.path.exists(index_path):
        return {}
    with open(index_path, 'rb') as f:
        return pickle.load(f)


def clear_gallery_index(index_path: str) -> None:
    """Remove the persisted gallery index if it exists."""
    if os.path.exists(index_path):
        try:
            os.remove(index_path)
        except OSError:
            pass

