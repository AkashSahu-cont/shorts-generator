# ⚡ ShortCraft AI - YouTube to Multiple Shorts Generator & Downloader

Ek powerful aur modern web application jo kisi bhi YouTube video link se automatically multiple 9:16 vertical Short videos generate karti hai aur direct MP4 download karne ki suvidha deti hai.

---

## 🌟 Key Features (Khasiyat)

1. **YouTube Video Link Input**:
   - Kisi bhi YouTube video ka link dalein (podcast, comedy, tech tutorial, speeches, etc.).
   - Instant video metadata preview (Title, Channel name, Duration, Views, Thumbnail).
   - "Paste" button clipboard se automatic link copy karne ke liye.
   - Quick sample buttons 1-click testing ke liye.

2. **Multiple Shorts Generation**:
   - **Number of Shorts**: Aap choose kar sakte hain ki kitne shorts generate karne hain (1 se 5 Shorts).
   - **Duration Selection**: Har short ki length customize karein (15 sec, 30 sec, 45 sec, ya 60 sec).
   - **Highlight Detection**: Video ke high-energy aur engaging parts ko automatically scan karke separate clips me slice karta hai.

3. **9:16 Vertical Video Styling (Reels & Shorts Ready)**:
   - **Blurred Background + Crisp Focused Center** (Opus Clip / CapCut Studio Style - horizontal video ko bina crop kiye premium vertical look deta hai).
   - **Smart Center Crop** (Full 9:16 screen fill).
   - **Clean Cinematic Letterbox** (Black bars top & bottom).
   - **Highlight Hook Title Overlay**: Short ke upar attention-grabbing title banner.

4. **✨ AI Speech Transcription & Animated Subtitles (Optional Option)**:
   - **Optional Toggle**: Aapki marzi ke mutabiq — jab ON karenge tabhi subtitles video me burn honge.
   - **Viral Styles**:
     - 🔥 **Viral Hormozi**: Bold Yellow Pop & White text with black outline.
     - ⚡ **Cyber Neon**: Electric Cyan glow styling.
     - 🎤 **Karaoke Glow**: Active word glow highlight.
     - 🤍 **Clean Pill Box**: Modern minimal badge.
     - 💥 **Fire Energy**: Flame red/yellow accents.
   - **Language Support**: Auto-detect, Hindi (हिंदी / Hinglish), English, Spanish, etc.
   - **Positioning**: Lower Safe Zone (Shorts/Reels UI icons se bachakar) ya Center Screen.
   - **Interactive Live Preview**: Options select karte waqt live animated preview.

5. **1-Click Download System**:
   - Har generated short ka **Direct MP4 Download** button.
   - Sabhi shorts ko ek sath download karne ke liye **"Download All (.ZIP)"** button.
   - In-browser interactive 9:16 vertical video player with sound, playback controls, and viral score meter.

6. **Direct Video Upload Alternative**:
   - Agar aapke paas computer me local video file (.mp4, .mov, .webm) hai, toh use bhi drag & drop karke shorts bana sakte hain.

---

## 🚀 Kaise Start Karein (How to Run)

### Tarika 1: Double Click (Sabse Aasan)
Workspace folder me maujood `run.bat` file par double click karein. Server shuru ho jayega!

### Tarika 2: Terminal / Command Line
1. Terminal open karein aur project folder me jayein:
   ```bash
   cd "c:\Users\AKASH\OneDrive\Desktop\short generator"
   ```
2. Python application run karein:
   ```bash
   python app.py
   ```
3. Browser me open karein:
   👉 **[http://localhost:5000](http://localhost:5000)**

---

## 📂 Project Structure

```
short generator/
│
├── app.py                     # Flask Web API server & background task runner
├── shorts_engine.py           # Core video processing engine (yt-dlp + FFmpeg 7.1)
├── run.bat                    # Windows 1-click launcher
├── requirements.txt           # Python dependencies
│
├── static/
│   ├── index.html             # Sleek dark cyberpunk creator UI
│   ├── css/
│   │   └── style.css          # Glassmorphic responsive styling & animations
│   ├── js/
│   │   └── app.js             # Live progress polling, video preview & downloads
│   └── generated/             # Generated 9:16 Short videos & ZIP files
│
└── downloads/                 # Downloaded source video streams
```

---

## 🛠️ Technologies Used
- **Backend**: Python 3.14, Flask, yt-dlp, FFmpeg 7.1 (via imageio-ffmpeg)
- **Frontend**: Modern HTML5, Vanilla CSS3 (Glassmorphism & Obsidian Dark Theme), JavaScript ES6+
- **Video Formatting**: H.264 / AAC 9:16 Vertical Rendering
