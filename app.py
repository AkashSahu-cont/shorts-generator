import os
import uuid
import threading
import time
from flask import Flask, request, jsonify, send_from_directory, send_file, session, redirect, url_for, render_template_string
from flask_cors import CORS
from werkzeug.utils import secure_filename
from shorts_engine import ShortsEngine, OUTPUTS_DIR, DOWNLOADS_DIR

# ── Login Credentials ─────────────────────────────────────────────────────────
# Override via environment variables for production security
APP_EMAIL    = os.environ.get("APP_EMAIL",    "admin@shortcraft.ai")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "shortcraft2026")
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder="static", static_url_path="")
app.url_map.strict_slashes = False
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "shortcraft-ai-secret-key-2026-change-in-prod")
CORS(app)

engine = ShortsEngine()

# Local output folder (used on cloud servers)
D_DRIVE_FOLDER = None  # D: Drive not available on cloud/Linux servers

# In-memory task tracker
tasks = {}

def login_required(f):
    """Decorator: redirect to /login if no active session."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
@app.route("/home")
@app.route("/dashboard")
@app.route("/app")
@app.route("/index.html")
@login_required
def index():
    return app.send_static_file("index.html")


# ── Auth Routes ───────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET"])
@app.route("/login.html", methods=["GET"])
def login_page():
    if session.get("logged_in"):
        return redirect("/")
    return app.send_static_file("login.html")


@app.route("/login", methods=["POST"])
def login_submit():
    email    = (request.form.get("email", "") or "").strip().lower()
    password = (request.form.get("password", "") or "").strip()

    if email == APP_EMAIL.lower() and password == APP_PASSWORD:
        session["logged_in"] = True
        session["user_email"] = email
        if request.form.get("remember"):
            # 30-day persistent session
            session.permanent = True
            app.permanent_session_lifetime = __import__("datetime").timedelta(days=30)
        return redirect("/")
    else:
        return redirect("/login?error=1")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.errorhandler(404)
def handle_404(e):
    """Catch-all 404 handler to redirect unknown page URLs to login or home."""
    if request.path.startswith("/api/") or request.path.startswith("/generated/"):
        return jsonify({"error": "Resource not found"}), 404
    if session.get("logged_in"):
        return redirect("/")
    return redirect("/login")


@app.route("/api/auth/status", methods=["GET"])
def auth_status():
    return jsonify({"logged_in": bool(session.get("logged_in")), "email": session.get("user_email", "")})

@app.route("/generated/<path:filename>")
def serve_generated_video(filename):
    return send_from_directory(OUTPUTS_DIR, filename, conditional=True)

@app.route("/api/open-folder", methods=["POST"])
def open_folder():
    # os.startfile is Windows-only, not available on cloud/Linux servers
    return jsonify({"success": False, "error": "Folder open not supported on cloud server. Please download videos directly."}), 400

@app.route("/api/info", methods=["POST"])
def get_info():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "Please provide a valid YouTube URL"}), 400

    try:
        info = engine.get_video_info(url)
        return jsonify({"success": True, "info": info})
    except Exception as e:
        return jsonify({"error": f"Failed to get video info: {str(e)}"}), 500

def run_generation_task(
    task_id: str,
    url: str,
    local_filepath: str,
    num_shorts: int,
    duration_sec: int,
    style: str,
    overlay_title: bool,
    enable_subtitles: bool = False,
    subtitle_style: str = "hormozi",
    subtitle_lang: str = "auto",
    subtitle_pos: str = "bottom"
):
    task = tasks[task_id]
    try:
        task["status"] = "processing"
        task["progress"] = 5
        task["message"] = "Initializing video pipeline..."

        source_file = local_filepath
        video_title = "Video Clip"

        # Step 1: Download or load video
        if url:
            task["message"] = "Fetching YouTube stream..."
            def dl_progress(pct, msg):
                task["progress"] = min(35, 5 + pct)
                task["message"] = msg
            
            source_file = engine.download_video(url, task_id, dl_progress, fetch_subtitles=enable_subtitles)
            task["progress"] = 35
            task["message"] = "Download complete. Analyzing video structure..."
        else:
            task["progress"] = 30
            task["message"] = "Video uploaded. Analyzing structure..."

        # Step 2: Measure duration & calculate highlights
        total_duration = engine.get_media_duration(source_file)
        if total_duration <= 0:
            total_duration = 60.0

        task["progress"] = 40
        task["message"] = f"Detected {int(total_duration)}s video. Generating {num_shorts} highlight segments..."
        
        segments = engine.analyze_highlights(source_file, total_duration, num_shorts, duration_sec)
        
        # Step 3: Render each short
        generated_clips = []
        progress_per_clip = 50.0 / max(1, len(segments))

        for idx, seg in enumerate(segments):
            clip_idx = idx + 1
            clip_name = f"short_{task_id[:8]}_{clip_idx}.mp4"
            clip_output = os.path.join(OUTPUTS_DIR, clip_name)
            
            sub_info = " + Animated Subtitles" if enable_subtitles else ""
            task["message"] = f"Rendering Short #{clip_idx}/{len(segments)} ({seg['label']}{sub_info})..."
            
            hook_title = seg['label'].upper() if overlay_title else None
            
            success = engine.generate_short(
                source_path=source_file,
                start_time=seg["start"],
                duration=seg["duration"],
                output_path=clip_output,
                style=style,
                title_text=hook_title,
                enable_subtitles=enable_subtitles,
                subtitle_style=subtitle_style,
                subtitle_lang=subtitle_lang,
                subtitle_pos=subtitle_pos,
                task_id=task_id,
                clip_idx=clip_idx
            )

            if success:
                file_size_mb = round(os.path.getsize(clip_output) / (1024 * 1024), 2)

                generated_clips.append({
                    "id": f"{task_id}_{clip_idx}",
                    "filename": clip_name,
                    "download_url": f"/api/download/{clip_name}",
                    "stream_url": f"/generated/{clip_name}",
                    "label": seg["label"],
                    "start": seg["start"],
                    "end": seg["end"],
                    "duration": seg["duration"],
                    "viral_score": seg["score"],
                    "file_size": f"{file_size_mb} MB",
                    "subtitles_enabled": enable_subtitles,
                    "d_drive_saved": False
                })
            
            task["progress"] = min(92, int(40 + (idx + 1) * progress_per_clip))

        # Step 4: Create zip archive
        task["message"] = "Creating bundled ZIP package..."
        zip_path = engine.create_zip(task_id, [os.path.join(OUTPUTS_DIR, c["filename"]) for c in generated_clips])
        zip_filename = os.path.basename(zip_path)

        task["progress"] = 100
        task["status"] = "completed"
        task["message"] = f"Successfully generated {len(generated_clips)} Short videos!"
        task["shorts"] = generated_clips
        task["zip_url"] = f"/api/download/{zip_filename}"

    except Exception as e:
        task["status"] = "failed"
        task["message"] = f"Error: {str(e)}"
        task["error"] = str(e)

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    num_shorts = int(data.get("num_shorts", 3))
    duration_sec = int(data.get("duration", 30))
    style = data.get("style", "crop") # crop (Full Screen), blur_bg, letterbox
    overlay_title = bool(data.get("overlay_title", True))
    
    # Subtitle Options
    enable_subtitles = bool(data.get("enable_subtitles", False))
    subtitle_style = str(data.get("subtitle_style", "hormozi"))
    subtitle_lang = str(data.get("subtitle_lang", "auto"))
    subtitle_pos = str(data.get("subtitle_pos", "bottom"))

    if not url:
        return jsonify({"error": "YouTube URL is required."}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "id": task_id,
        "status": "queued",
        "progress": 0,
        "message": "Queued for processing...",
        "shorts": [],
        "created_at": time.time()
    }

    # Start generation thread
    thread = threading.Thread(
        target=run_generation_task,
        args=(
            task_id, url, None, num_shorts, duration_sec, style, overlay_title,
            enable_subtitles, subtitle_style, subtitle_lang, subtitle_pos
        ),
        daemon=True
    )
    thread.start()

    return jsonify({"success": True, "task_id": task_id})

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    task_id = str(uuid.uuid4())
    saved_path = os.path.join(DOWNLOADS_DIR, f"{task_id}_{filename}")
    file.save(saved_path)

    num_shorts = int(request.form.get("num_shorts", 3))
    duration_sec = int(request.form.get("duration", 30))
    style = request.form.get("style", "crop")
    overlay_title = request.form.get("overlay_title", "true").lower() == "true"
    
    # Subtitle Options
    enable_subtitles = request.form.get("enable_subtitles", "false").lower() == "true"
    subtitle_style = request.form.get("subtitle_style", "hormozi")
    subtitle_lang = request.form.get("subtitle_lang", "auto")
    subtitle_pos = request.form.get("subtitle_pos", "bottom")

    tasks[task_id] = {
        "id": task_id,
        "status": "queued",
        "progress": 0,
        "message": "Uploaded file. Queued for processing...",
        "shorts": [],
        "created_at": time.time()
    }

    thread = threading.Thread(
        target=run_generation_task,
        args=(
            task_id, None, saved_path, num_shorts, duration_sec, style, overlay_title,
            enable_subtitles, subtitle_style, subtitle_lang, subtitle_pos
        ),
        daemon=True
    )
    thread.start()

    return jsonify({"success": True, "task_id": task_id})

@app.route("/api/progress/<task_id>", methods=["GET"])
def get_progress(task_id):
    if task_id not in tasks:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(tasks[task_id])

@app.route("/api/download/<filename>", methods=["GET"])
def download_file(filename):
    safe_filename = secure_filename(filename)
    file_path = os.path.join(OUTPUTS_DIR, safe_filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=safe_filename)
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    print("Starting YouTube Shorts Generator server on http://localhost:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
