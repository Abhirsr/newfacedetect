"""
Script for capturing a face from webcam, extracting encodings, and matching against gallery images.

This module provides face recognition functionality using the face_recognition library.
It can work in two modes:
1. Standalone mode: Captures frames from webcam and matches against gallery
2. Function mode: Processes pre-captured frames from a directory
"""

import cv2
import face_recognition
import numpy as np
import os
import shutil
import time
from typing import Dict, List

from gallery_index import load_gallery_index


def run_face_matching(reference_frames_dir, gallery_folder):
    """
    Given a directory of reference frames (images), extract face encodings and match 
    against gallery images in the specified gallery_folder.
    
    This function performs the core face matching logic:
    1. Loads reference frames from the specified directory
    2. Extracts face encodings from all reference frames
    3. Processes each gallery image to find matching faces
    4. Saves matched images with bounding boxes and confidence scores
    
    Args:
        reference_frames_dir (str): Path to directory containing reference frame images
        gallery_folder (str): Path to directory containing gallery images to match against
    
    Returns:
        int: Number of gallery images that contained at least one matching face
    """
    # =============================================================================
    # CONFIGURATION
    # =============================================================================
    
    # Threshold for face matching (lower = more strict matching)
    MATCH_THRESHOLD = 0.45
    
    # Output folder for matched images
    MATCHED_FOLDER = "static/matched"
    
    # =============================================================================
    # PREPARE OUTPUT FOLDER
    # =============================================================================
    
    # Clear and recreate matched_faces folder
    if os.path.exists(MATCHED_FOLDER):
        shutil.rmtree(MATCHED_FOLDER)
    os.makedirs(MATCHED_FOLDER)
    
    # =============================================================================
    # STEP 1: LOAD REFERENCE FRAMES
    # =============================================================================
    
    captured_frames = []
    
    # Load all image files from reference directory
    for fname in sorted(os.listdir(reference_frames_dir)):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            frame = cv2.imread(os.path.join(reference_frames_dir, fname))
            if frame is not None:
                captured_frames.append(frame)
    
    print(f"✅ Loaded {len(captured_frames)} reference frames from {reference_frames_dir}.")
    
    if not captured_frames:
        print("❌ No frames found in reference directory.")
        return 0
    
    # =============================================================================
    # STEP 2: EXTRACT FACE ENCODINGS FROM REFERENCE FRAMES
    # =============================================================================
    
    ref_encodings = []
    
    # Process each reference frame to extract face encodings
    for frame in captured_frames:
        # Convert BGR to RGB (face_recognition expects RGB)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Extract face encodings from the frame
        faces = face_recognition.face_encodings(rgb)
        ref_encodings.extend(faces)
    
    if not ref_encodings:
        print("❌ No face detected in reference frames.")
        return 0
    
    print(f"🧠 Stored {len(ref_encodings)} reference encodings.\n")
    
    # =============================================================================
    # STEP 3: MATCH AGAINST GALLERY IMAGES
    # =============================================================================
    
    match_count = 0
    
    # Try to use precomputed gallery index if available
    index_path = os.path.join('static', 'models', 'gallery_index.pkl')
    gallery_index: Dict[str, Dict[str, List]] = load_gallery_index(index_path)

    # Process each image in the gallery folder
    for filename in os.listdir(gallery_folder):
        path = os.path.join(gallery_folder, filename)
        img_bgr = cv2.imread(path)
        if img_bgr is None:
            continue

        # Convert BGR to RGB for saving clean copy later
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        # Prefer precomputed encodings/locations from index
        if filename in gallery_index:
            face_locations = gallery_index[filename].get('locations', [])
            face_encodings = gallery_index[filename].get('encodings', [])
        else:
            # Fallback to on-the-fly detection if not indexed
            face_locations = face_recognition.face_locations(img_rgb)
            face_encodings = face_recognition.face_encodings(img_rgb, face_locations)
        
        matched = False
        
        # Check each face in the gallery image against reference encodings
        for i, enc in enumerate(face_encodings):
            # Calculate distances to all reference encodings
            distances = [np.linalg.norm(enc - ref) for ref in ref_encodings]
            min_dist = min(distances)
            
            # If distance is below threshold, we have a match
            if min_dist < MATCH_THRESHOLD:
                matched = True
                
                # Draw bounding box around matched face
                top, right, bottom, left = face_locations[i]
                cv2.rectangle(img_bgr, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # Add confidence score text
                cv2.putText(img_bgr, f"{min_dist:.2f}", (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # If any face in this image matched, save the image
        if matched:
            # Save clean version (RGB) without bounding boxes
            out_clean_path = os.path.join(MATCHED_FOLDER, f"clean_{filename}")
            cv2.imwrite(out_clean_path, img_rgb[:, :, ::-1])
            
            # Save annotated version (BGR) with bounding boxes
            out_path = os.path.join(MATCHED_FOLDER, filename)
            cv2.imwrite(out_path, img_bgr)
            
            match_count += 1
    
    # =============================================================================
    # STEP 4: REPORT RESULTS
    # =============================================================================
    
    print(f"\n🎯 {match_count} group image(s) with at least one match saved to '{MATCHED_FOLDER}'.")
    
    if match_count == 0:
        print("🚫 No perfect matches found.")
    
    return match_count


# =============================================================================
# STANDALONE SCRIPT MODE FOR DEBUGGING
# =============================================================================

if __name__ == "__main__":
    """
    Standalone mode: Captures frames from webcam and performs face matching.
    
    This mode is useful for testing and debugging the face matching functionality.
    It captures frames for 5 seconds and then processes them against the gallery.
    """
    
    # =============================================================================
    # CONFIGURATION FOR STANDALONE MODE
    # =============================================================================
    
    # Frame capture interval (capture every N frames)
    FRAME_INTERVAL = 2
    
    # Duration to capture frames (in seconds)
    CAPTURE_DURATION = 5
    
    print("📷 Starting 5-second face capture. Look at the camera...")
    
    # =============================================================================
    # INITIALIZE CAMERA
    # =============================================================================
    
    cap = cv2.VideoCapture(0)
    start_time = time.time()
    captured_frames = []
    frame_count = 0
    
    # =============================================================================
    # CAPTURE FRAMES
    # =============================================================================
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        elapsed = time.time() - start_time
        if elapsed > CAPTURE_DURATION:
            break
        
        # Capture frame at specified interval
        if frame_count % FRAME_INTERVAL == 0:
            captured_frames.append(frame.copy())
        
        # Display live feed
        cv2.imshow("Capturing Face (Look at the Camera)", frame)
        
        # Check for quit key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        frame_count += 1
    
    # =============================================================================
    # CLEANUP AND PROCESSING
    # =============================================================================
    
    # Release camera and close windows
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"📸 Captured {len(captured_frames)} frames.")
    
    if len(captured_frames) == 0:
        print("❌ No frames captured. Check camera connection.")
        exit(1)
    
    # =============================================================================
    # SAVE CAPTURED FRAMES
    # =============================================================================
    
    # Create temporary directory for captured frames
    temp_dir = "temp_captured_frames"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save captured frames as images
    for i, frame in enumerate(captured_frames):
        filename = os.path.join(temp_dir, f"frame_{i:03d}.jpg")
        cv2.imwrite(filename, frame)
    
    print(f"💾 Saved {len(captured_frames)} frames to {temp_dir}/")
    
    # =============================================================================
    # PERFORM FACE MATCHING
    # =============================================================================
    
    # Use the single gallery folder
    gallery_folder = "static/gallery"
    
    if not os.path.exists(gallery_folder):
        print(f"❌ Gallery folder '{gallery_folder}' not found.")
        print("Please upload gallery images via the admin dashboard.")
        exit(1)
    
    # Run face matching
    match_count = run_face_matching(temp_dir, gallery_folder)
    
    # =============================================================================
    # CLEANUP TEMPORARY FILES
    # =============================================================================
    
    # Remove temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    print(f"🧹 Cleaned up temporary files.")
    print(f"✅ Face matching complete. Found {match_count} matches.")