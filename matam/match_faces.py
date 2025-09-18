"""Face matching: extract encodings from reference frames and compare to preindexed gallery."""

import cv2
import face_recognition
import numpy as np
import os
import shutil
import time
from typing import Dict, List

from gallery_index import load_gallery_index


def run_face_matching(reference_frames_dir, gallery_folder):
    """Return count of gallery images with at least one face matching the reference set."""
    # Threshold for face matching (lower = more strict matching)
    MATCH_THRESHOLD = 0.45
    
    # Output folder for matched images
    MATCHED_FOLDER = "static/matched"
    
    # Clear and recreate matched output folder
    if os.path.exists(MATCHED_FOLDER):
        shutil.rmtree(MATCHED_FOLDER)
    os.makedirs(MATCHED_FOLDER)
    
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
    
    ref_encodings = []
    
    # Extract encodings from reference frames
    for frame in captured_frames:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_encodings(rgb)
        ref_encodings.extend(faces)
    
    if not ref_encodings:
        print("❌ No face detected in reference frames.")
        return 0
    
    print(f"🧠 Stored {len(ref_encodings)} reference encodings.\n")
    
    match_count = 0
    
    # Use precomputed gallery index
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

        # Use only precomputed encodings/locations from index; skip if not indexed
        if filename in gallery_index:
            face_locations = gallery_index[filename].get('locations', [])
            face_encodings = gallery_index[filename].get('encodings', [])
        else:
            continue
        
        matched = False
        
        # Compare each gallery face encoding to reference encodings
        for i, enc in enumerate(face_encodings):
            distances = [np.linalg.norm(enc - ref) for ref in ref_encodings]
            min_dist = min(distances)
            
            if min_dist < MATCH_THRESHOLD:
                matched = True
                
                top, right, bottom, left = face_locations[i]
                cv2.rectangle(img_bgr, (left, top), (right, bottom), (0, 255, 0), 2)
                
                cv2.putText(img_bgr, f"{min_dist:.2f}", (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # If any face matched, save clean and annotated outputs
        if matched:
            out_clean_path = os.path.join(MATCHED_FOLDER, f"clean_{filename}")
            cv2.imwrite(out_clean_path, img_rgb[:, :, ::-1])
            
            out_path = os.path.join(MATCHED_FOLDER, filename)
            cv2.imwrite(out_path, img_bgr)
            
            match_count += 1
    
    print(f"\n🎯 {match_count} group image(s) with at least one match saved to '{MATCHED_FOLDER}'.")
    
    if match_count == 0:
        print("🚫 No perfect matches found.")
    
    return match_count


# =============================================================================
# STANDALONE SCRIPT MODE FOR DEBUGGING
# =============================================================================

if __name__ == "__main__":
    """Standalone: capture frames for 5s, then run face matching and report count."""
    
    # Frame capture interval (capture every N frames)
    FRAME_INTERVAL = 2
    
    # Duration to capture frames (in seconds)
    CAPTURE_DURATION = 5
    
    print("📷 Starting 5-second face capture. Look at the camera...")
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    start_time = time.time()
    captured_frames = []
    frame_count = 0
    
    # Capture frames
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
    
    # Cleanup and processing
    # Release camera and close windows
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"📸 Captured {len(captured_frames)} frames.")
    
    if len(captured_frames) == 0:
        print("❌ No frames captured. Check camera connection.")
        exit(1)
    
    # Save captured frames
    # Create temporary directory for captured frames
    temp_dir = "temp_captured_frames"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save captured frames as images
    for i, frame in enumerate(captured_frames):
        filename = os.path.join(temp_dir, f"frame_{i:03d}.jpg")
        cv2.imwrite(filename, frame)
    
    print(f"💾 Saved {len(captured_frames)} frames to {temp_dir}/")
    
    # Perform face matching
    # Use the single gallery folder
    gallery_folder = "static/gallery"
    
    if not os.path.exists(gallery_folder):
        print(f"❌ Gallery folder '{gallery_folder}' not found.")
        print("Please upload gallery images via the admin dashboard.")
        exit(1)
    
    # Run face matching
    match_count = run_face_matching(temp_dir, gallery_folder)
    
    # Cleanup temporary files
    # Remove temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    print(f"🧹 Cleaned up temporary files.")
    print(f"✅ Face matching complete. Found {match_count} matches.")