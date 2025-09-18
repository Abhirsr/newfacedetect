/**
 * Main JavaScript file for the Face Matcher application.
 *
 * This file handles:
 * - Camera initialization and frame capture
 * - Face detection using face-api.js
 * - Communication with the Flask backend
 * - User interface interactions
 * - Email collection and result polling
 */

// =============================================================================
// GLOBAL VARIABLES AND ELEMENTS
// =============================================================================

const video = document.getElementById("video");
const formSection = document.getElementById("form-section");

// Application state variables
let storedEmail = null;
let emailSent = false;
let requestId = null;

// =============================================================================
// CAMERA INITIALIZATION
// =============================================================================

/**
 * Initialize camera with mobile-friendly settings.
 * Attempts to use front-facing camera on mobile devices.
 */
if (video) {
  navigator.mediaDevices
    .getUserMedia({ video: { facingMode: "user" } })
    .then((stream) => {
      video.srcObject = stream;
    })
    .catch((err) => {
      // Fallback to default camera if facingMode is not supported
      navigator.mediaDevices
        .getUserMedia({ video: true })
        .then((stream) => {
          video.srcObject = stream;
        })
        .catch((err2) => {
          console.error("Camera access denied:", err2);
          alert("Please allow camera access to continue.");
        });
    });
}

// =============================================================================
// FACE DETECTION AND MODEL LOADING
// =============================================================================

/**
 * Load face detection models from the static/models directory.
 * Required for face detection functionality.
 */
async function loadModels() {
  await faceapi.nets.tinyFaceDetector.loadFromUri("/static/models");
}

// =============================================================================
// PROGRESS BAR SETUP
// =============================================================================

/**
 * Create and add a progress bar for frame capture visualization.
 * Shows the user the progress of the 5-second capture process.
 */
if (!document.getElementById("capture-progress")) {
  const progressBar = document.createElement("div");
  progressBar.id = "capture-progress";
  progressBar.style =
    "width: 100%; height: 8px; background: #eee; margin: 16px 0; display: none;";

  const fill = document.createElement("div");
  fill.id = "capture-progress-fill";
  fill.style =
    "height: 100%; width: 0; background: #4caf50; transition: width 0.1s;";

  progressBar.appendChild(fill);
  document.getElementById("form-section").appendChild(progressBar);
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Generate a simple UUID for request identification.
 * Creates a unique identifier for each face matching session.
 *
 * @returns {string} A UUID string
 */
function generateUUID() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    var r = (Math.random() * 16) | 0,
      v = c == "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// Track current request ID
let currentRequestId = null;

// =============================================================================
// MAIN CAPTURE FUNCTION
// =============================================================================

/**
 * Main function to capture frames from the camera and initiate face matching.
 *
 * This function:
 * 1. Shows a progress bar
 * 2. Loads face detection models
 * 3. Captures frames for 5 seconds
 * 4. Uploads frames to the backend
 * 5. Shows email input form
 */
async function capture() {
  // Show progress bar
  const progressBar = document.getElementById("capture-progress");
  const fill = document.getElementById("capture-progress-fill");
  progressBar.style.display = "block";
  fill.style.width = "0";

  // Load face detection models
  await loadModels();

  // Generate a new request/session ID
  currentRequestId = generateUUID();

  // =============================================================================
  // FRAME CAPTURE CONFIGURATION
  // =============================================================================

  const duration = 5000; // Capture duration in milliseconds
  const start = Date.now();
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  let allFrames = [];
  let frameCount = 0;

  /**
   * Update the progress bar to show capture progress.
   */
  function updateBar() {
    const elapsed = Date.now() - start;
    fill.style.width = Math.min((elapsed / duration) * 100, 100) + "%";
  }

  // =============================================================================
  // FRAME CAPTURE LOOP
  // =============================================================================

  while (Date.now() - start < duration) {
    // Draw current video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to base64 data URL
    const frameData = canvas.toDataURL("image/jpeg", 0.8);
    allFrames.push(frameData);
    frameCount++;

    // Update progress bar
    updateBar();

    // Wait 20ms between frames (~50fps max)
    await new Promise((r) => setTimeout(r, 20));
  }

  // Hide progress bar
  progressBar.style.display = "none";

  // Show email input immediately after capture
  showEmailForm();

  // =============================================================================
  // UPLOAD FRAMES TO BACKEND
  // =============================================================================

  // Send frames to backend with request ID (do not wait for email input)
  fetch("/upload_frames", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ frames: allFrames, request_id: currentRequestId }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "no_face") {
        alert("❌ No face found. Try again.");
      } else if (data.status !== "ok") {
        alert("❌ Upload failed: " + (data.message || "Unknown error"));
      }
    })
    .catch((err) => {
      alert("⚠️ Failed to upload frames. Try again.");
      console.error("Upload error:", err);
    });
}

// =============================================================================
// EMAIL HANDLING FUNCTIONS
// =============================================================================

/**
 * Show email input form after frame capture is complete.
 * Replaces the capture interface with email collection form.
 */
function showEmailForm() {
  formSection.innerHTML = `
        <p style="text-align:center; font-size: 18px;">📸 Captured! Enter your email to receive matched images.</p>
        <input type="email" id="userEmail" placeholder="Enter your email" style="margin-top: 20px; padding: 10px; width: 100%; font-size: 16px;" required>
        <button onclick="storeEmail()" class="btn" style="margin-top: 15px;">✅ Confirm Email</button>
    `;
}

/**
 * Store user email and initiate face matching process.
 * Sends email and request ID to backend to start processing.
 */
function storeEmail() {
  const email = document.getElementById("userEmail").value;

  // Validate email format
  if (!email || !email.includes("@")) {
    alert("Please enter a valid email.");
    return;
  }

  // Send email and request ID to backend
  fetch("/store_email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email, request_id: currentRequestId }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        requestId = data.request_id;
        localStorage.setItem("request_id", requestId);

        // Show success message
        formSection.innerHTML = `
                    <p style="text-align:center; font-size: 18px; color: green;">
                        ✅ Email stored. You'll receive your images once matching is ready.
                    </p>
                `;
      } else {
        alert("❌ Failed to store email on server.");
      }
    })
    .catch((err) => {
      console.error("Error storing email:", err);
      alert("⚠️ Could not store email.");
    });
}

// =============================================================================
// RESULT POLLING FUNCTIONS
// =============================================================================

/**
 * Poll the backend for request status until results are ready.
 * Checks the status of the face matching request periodically.
 */
function pollForResults() {
  requestId = requestId || localStorage.getItem("request_id");

  if (!requestId) {
    alert("No request ID found. Please start the process again.");
    return;
  }

  const interval = setInterval(() => {
    fetch(`/status?request_id=${requestId}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "ready" && storedEmail && !emailSent) {
          clearInterval(interval);
          sendEmailIfStored();
        }
      })
      .catch((err) => {
        console.error("Polling error:", err);
      });
  }, 3000); // Poll every 3 seconds
}

// =============================================================================
// ADMIN FUNCTIONS
// =============================================================================

/**
 * Clear all images from the gallery folder.
 * Admin function to reset the gallery completely.
 */
function clearGallery() {
  if (
    !confirm(
      "⚠️ Are you sure you want to delete all images in the gallery folder?"
    )
  )
    return;

  fetch("/clear_gallery", { method: "POST" })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        alert("✅ Gallery folder cleared.");
      } else {
        alert("❌ Failed to clear gallery: " + data.message);
      }
    })
    .catch((err) => {
      console.error("Clear gallery error:", err);
      alert("⚠️ Error clearing gallery.");
    });
}

/**
 * Reset the application state.
 * Clears matched images and resets flags.
 */
function reset() {
  if (!confirm("⚠️ Are you sure you want to reset the application?")) return;

  fetch("/reset", { method: "POST" })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        alert("✅ Application reset successfully.");
      } else {
        alert("❌ Failed to reset: " + data.message);
      }
    })
    .catch((err) => {
      console.error("Reset error:", err);
      alert("⚠️ Error resetting application.");
    });
}

// =============================================================================
// EMAIL SENDING FUNCTIONS
// =============================================================================

/**
 * Send email if email is stored and not already sent.
 * Legacy function for the old email workflow.
 */
function sendEmailIfStored() {
  if (storedEmail && !emailSent) {
    fetch("/send_email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: storedEmail }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "ok") {
          emailSent = true;
          alert("✅ Email sent! Check your inbox.");
        } else {
          alert("❌ Failed to send email: " + data.message);
        }
      })
      .catch((err) => {
        console.error("Send email error:", err);
        alert("⚠️ Error sending email.");
      });
  }
}

// =============================================================================
// INITIALIZATION
// =============================================================================

/**
 * Initialize the application when the page loads.
 * Sets up event listeners and initial state.
 */
document.addEventListener("DOMContentLoaded", function () {
  // Check if there's a stored request ID
  const storedRequestId = localStorage.getItem("request_id");
  if (storedRequestId) {
    requestId = storedRequestId;
  }

  console.log("Face Matcher application initialized.");
});
