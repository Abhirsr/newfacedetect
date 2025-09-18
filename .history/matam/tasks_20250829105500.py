"""
Background task for zipping matched images, uploading to Supabase, and emailing results to the user.

This module handles the asynchronous processing of user requests after face matching is complete.
It performs the following operations:
1. Creates a zip file of matched images
2. Uploads the zip to Supabase Storage
3. Sends an email to the user with the download link
4. Updates the request status in the database

The module uses multiprocessing to handle background tasks efficiently.
"""

import os
import zipfile
import tempfile
import multiprocessing

# Set multiprocessing start method for compatibility
multiprocessing.set_start_method('forkserver', force=True)

# Import shared context
from context import supabase, mail, Message


def process_user_request(request_id):
    """
    Processes a user request to zip matched images, upload to Supabase, and send email.
    
    This function is the main entry point for processing a completed face matching request.
    It handles the entire pipeline from creating the zip file to sending the email.
    
    Args:
        request_id (str): The unique ID of the user request to process.
    
    The function performs the following steps:
    1. Fetches the user request details from Supabase
    2. Validates that email and matched files exist
    3. Creates a zip file containing all matched images
    4. Uploads the zip to Supabase Storage
    5. Sends an email to the user with the download link
    6. Updates the request status to 'done'
    7. Cleans up temporary files
    
    If any step fails, the request is marked as 'error' with an error message.
    """
    
    # =============================================================================
    # STEP 1: FETCH USER REQUEST DETAILS
    # =============================================================================
    
    # Fetch the user request row from Supabase database
    row = supabase.table('user_requests').select('*').eq('id', request_id).single().execute().data
    
    if not row:
        # Mark request as error if not found
        supabase.table('user_requests').update({
            'status': 'error', 
            'error_message': 'Request not found.'
        }).eq('id', request_id).execute()
        print(f"[ERROR] Request {request_id} not found.")
        return
    
    # Extract request details
    recipient = row['email']
    selected_images = row.get('matched_files', [])
    
    # =============================================================================
    # STEP 2: VALIDATE REQUEST DATA
    # =============================================================================
    
    # Check if email is provided
    if not recipient:
        supabase.table('user_requests').update({
            'status': 'error', 
            'error_message': 'No email provided.'
        }).eq('id', request_id).execute()
        print(f"[ERROR] Request {request_id}: No email provided.")
        return
    
    # Check if matched images exist
    if not selected_images:
        supabase.table('user_requests').update({
            'status': 'error', 
            'error_message': 'No matched images found.'
        }).eq('id', request_id).execute()
        print(f"[ERROR] Request {request_id}: No matched images found.")
        return
    
    # =============================================================================
    # STEP 3: CREATE ZIP FILE
    # =============================================================================
    
    # Define paths
    MATCHED_FOLDER = 'static/matched'
    image_paths = [os.path.join(MATCHED_FOLDER, f) for f in selected_images]
    
    try:
        # Create a temporary zip file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip, 'w') as zipf:
                # Add each matched image to the zip with a clean filename
                for idx, file_path in enumerate(image_paths, 1):
                    ext = os.path.splitext(file_path)[1]
                    new_name = f"matched_{idx}{ext}"
                    zipf.write(file_path, new_name)
            
            zip_path = tmp_zip.name
        
        # =============================================================================
        # STEP 4: UPLOAD TO SUPABASE STORAGE
        # =============================================================================
        
        # Define storage bucket and filename
        bucket_name = "matched-results"
        zip_filename = f"matched_{recipient.replace('@', '_').replace('.', '_')}_{request_id}.zip"
        
        # Upload the zip file to Supabase Storage
        with open(zip_path, "rb") as f:
            upload_response = supabase.storage.from_(bucket_name).upload(
                zip_filename, f, {"content-type": "application/zip", "x-upsert": "true"}
            )
        
        # =============================================================================
        # STEP 5: GET PUBLIC DOWNLOAD URL
        # =============================================================================
        
        # Get the public URL for the uploaded zip file
        public_url = supabase.storage.from_(bucket_name).get_public_url(zip_filename)
        
        # =============================================================================
        # STEP 6: SEND EMAIL TO USER
        # =============================================================================
        
        # Create and send email with download link
        msg = Message("Face Match Results", recipients=[recipient])
        msg.body = f"\U0001F4C1 Your matched images are here:\n\n{public_url}"
        mail.send(msg)
        
        # =============================================================================
        # STEP 7: UPDATE REQUEST STATUS
        # =============================================================================
        
        # Update the user request row with success status and zip URL
        supabase.table('user_requests').update({
            'zip_url': public_url,
            'status': 'done',
            'error_message': ''
        }).eq('id', request_id).execute()
        
        # =============================================================================
        # STEP 8: CLEANUP
        # =============================================================================
        
        # Remove the temporary zip file
        os.remove(zip_path)
        
        print(f"[SUCCESS] Request {request_id}: Processing completed successfully.")
        
    except Exception as e:
        # =============================================================================
        # ERROR HANDLING
        # =============================================================================
        
        # On any error, mark the request as error and log the reason
        supabase.table('user_requests').update({
            'status': 'error', 
            'error_message': str(e)
        }).eq('id', request_id).execute()
        
        print(f"[ERROR] Request {request_id}: Exception occurred: {e}")
        
        # Clean up temporary file if it exists
        if 'zip_path' in locals():
            try:
                os.remove(zip_path) 