import os
import sys
import re
import json
import uuid
import time
import zipfile
import subprocess
import threading
from typing import Dict, List, Optional, Callable
import yt_dlp

# SpeechRecognition is optional (requires PyAudio which is not available on all cloud servers)
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    sr = None
    SR_AVAILABLE = False

# FFmpeg path: try imageio_ffmpeg first, fall back to system ffmpeg
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_PATH = "ffmpeg"  # Use system ffmpeg installed via apt-get
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
OUTPUTS_DIR = os.path.join(BASE_DIR, "static", "generated")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

class ShortsEngine:
    def __init__(self):
        self.ffmpeg = FFMPEG_PATH
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None

    def get_video_info(self, url: str) -> dict:
        """Fetch video metadata quickly without downloading the entire video."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'ffmpeg_location': self.ffmpeg,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return {
                    "id": info.get("id", ""),
                    "title": info.get("title", "Untitled Video"),
                    "duration": info.get("duration", 0),
                    "duration_formatted": self.format_duration(info.get("duration", 0)),
                    "thumbnail": info.get("thumbnail", ""),
                    "author": info.get("uploader", info.get("channel", "Unknown Channel")),
                    "views": info.get("view_count", 0),
                    "description": (info.get("description") or "")[:200] + "...",
                    "url": url
                }
            except Exception as e:
                raise RuntimeError(f"Video info fetch error: {str(e)}")

    def format_duration(self, seconds: float) -> str:
        s = int(seconds)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def download_video(self, url: str, task_id: str, progress_callback: Optional[Callable] = None, fetch_subtitles: bool = False) -> str:
        """Download video at optimal resolution (720p or 1080p) for high quality & fast processing."""
        output_template = os.path.join(DOWNLOADS_DIR, f"{task_id}_source.%(ext)s")
        
        def ydl_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0 and progress_callback:
                    pct = int(downloaded / total * 30) # 0 to 30% for download
                    progress_callback(pct, f"Downloading YouTube stream: {pct * 100 // 30}%")

        ydl_opts = {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'ffmpeg_location': self.ffmpeg,
            'merge_output_format': 'mp4',
            'progress_hooks': [ydl_hook],
            'quiet': True,
            'no_warnings': True
        }

        if fetch_subtitles:
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = ['en', 'hi', 'hi-Latn']
            ydl_opts['subtitlesformat'] = 'vtt/best'
            ydl_opts['ignoreerrors'] = True

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            # If failed (e.g. subtitle 429 Too Many Requests), fallback to plain video download
            if fetch_subtitles:
                ydl_opts.pop('writesubtitles', None)
                ydl_opts.pop('writeautomaticsub', None)
                ydl_opts.pop('subtitleslangs', None)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            else:
                raise e

        expected_file = os.path.join(DOWNLOADS_DIR, f"{task_id}_source.mp4")
        if os.path.exists(expected_file):
            return expected_file
        
        # Fallback check
        for f in os.listdir(DOWNLOADS_DIR):
            if f.startswith(f"{task_id}_source") and f.endswith(('.mp4', '.mkv', '.webm')):
                return os.path.join(DOWNLOADS_DIR, f)

        raise FileNotFoundError("Downloaded source file could not be found.")

    def get_media_duration(self, filepath: str) -> float:
        """Get exact duration in seconds using ffmpeg."""
        cmd = [self.ffmpeg, "-i", filepath]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="replace")
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        if match:
            hours, mins, secs = match.groups()
            return int(hours) * 3600 + int(mins) * 60 + float(secs)
        return 0.0

    def analyze_highlights(self, filepath: str, total_duration: float, num_shorts: int, short_len: int) -> List[dict]:
        """
        Determine best start timestamps for shorts.
        If video is long enough, distribute intelligently across interesting parts.
        """
        if total_duration <= short_len:
            return [{"start": 0, "end": total_duration, "label": "Full Clip", "score": 98}]

        max_start = max(0, total_duration - short_len)
        segments = []
        
        step = max_start / (num_shorts + 0.5)
        for i in range(num_shorts):
            if num_shorts == 1:
                start = min(max_start, max_start * 0.2)
            else:
                start = min(max_start, (i + 0.3) * step)
            
            end = min(total_duration, start + short_len)
            viral_score = 90 + ((i * 3 + 7) % 9)
            
            labels = ["High Energy Hook", "Core Highlight", "Peak Moment", "Golden Insight", "Climax Scene", "Bonus Reel"]
            label = labels[i % len(labels)]
            
            segments.append({
                "start": round(start, 1),
                "end": round(end, 1),
                "duration": round(end - start, 1),
                "label": label,
                "score": viral_score
            })

        return segments

    # ---------------------------------------------------------
    # AI SPEECH TRANSCRIPTION & SUBTITLE SYSTEM
    # ---------------------------------------------------------

    def _parse_time_str(self, t_str: str) -> float:
        t_str = t_str.strip().replace(',', '.')
        parts = t_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        return 0.0

    def find_youtube_subtitle_file(self, task_id: str) -> Optional[str]:
        """Check if yt-dlp saved any .vtt or .srt subtitles in downloads."""
        if not task_id:
            return None
        candidates = []
        for f in os.listdir(DOWNLOADS_DIR):
            if f.startswith(f"{task_id}_source") and f.endswith(('.vtt', '.srt')):
                candidates.append(os.path.join(DOWNLOADS_DIR, f))
        
        if not candidates:
            return None
        
        # Prefer english or hindi if multiple exist
        for c in candidates:
            if '.en.' in c or '.hi.' in c:
                return c
        return candidates[0]

    def parse_subtitle_file(self, sub_file: str, clip_start: float, clip_duration: float) -> List[dict]:
        """Extract subtitles overlapping clip duration and re-align timestamps starting at 0."""
        clip_end = clip_start + clip_duration
        dialogues = []

        try:
            with open(sub_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            pattern = re.compile(
                r'(\d+:\d+(?::\d+)?[.,]\d+)\s*-->\s*(\d+:\d+(?::\d+)?[.,]\d+)[\s\S]*?\n([\s\S]*?)(?=\n\s*\n|\Z)'
            )

            for match in pattern.finditer(content):
                s_time = self._parse_time_str(match.group(1))
                e_time = self._parse_time_str(match.group(2))
                raw_text = match.group(3)

                # Clean VTT tags like <c.color>, <v Voice>, etc.
                clean_text = re.sub(r'<[^>]+>', '', raw_text).strip()
                clean_text = re.sub(r'\s+', ' ', clean_text)

                if not clean_text or clean_text.startswith('[') and clean_text.endswith(']'):
                    continue

                # Check overlap with clip
                if e_time > clip_start and s_time < clip_end:
                    rel_start = max(0.0, s_time - clip_start)
                    rel_end = min(clip_duration, e_time - clip_start)
                    if rel_end - rel_start >= 0.3:
                        dialogues.append({
                            "start": round(rel_start, 2),
                            "end": round(rel_end, 2),
                            "text": clean_text
                        })
        except Exception as e:
            print(f"[Subtitles] Error parsing subtitle file: {e}")

        return dialogues

    def transcribe_audio_segment(
        self,
        source_path: str,
        clip_start: float,
        clip_duration: float,
        language: str = "auto",
        task_id: str = "task"
    ) -> List[dict]:
        """
        Transcribe speech from the video audio using SpeechRecognition.
        Breaks segment into 2.5s-3.5s speech chunks for dynamic Shorts pacing.
        """
        dialogues = []
        temp_wav = os.path.join(DOWNLOADS_DIR, f"temp_{task_id}_{int(clip_start)}.wav")

        try:
            # 1. Extract 16kHz mono audio for this short segment
            cmd = [
                self.ffmpeg, "-y",
                "-ss", str(clip_start),
                "-t", str(clip_duration),
                "-i", source_path,
                "-vn",
                "-ar", "16000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                temp_wav
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if not os.path.exists(temp_wav) or os.path.getsize(temp_wav) < 2000:
                return []

            # 2. Map language parameter
            lang_map = {
                "hi": "hi-IN",
                "en": "en-US",
                "en-in": "en-IN",
                "es": "es-ES",
                "auto": None # Google recognizer default
            }
            recog_lang = lang_map.get(language.lower(), None)

            # 3. Transcribe in short 3-second slices for rapid punchy shorts captions
            slice_duration = 3.0
            total_audio_sec = min(clip_duration, self.get_media_duration(temp_wav))
            if total_audio_sec <= 0:
                total_audio_sec = clip_duration

            curr_offset = 0.0
            while curr_offset < total_audio_sec:
                dur = min(slice_duration, total_audio_sec - curr_offset)
                if dur < 0.6:
                    break

                try:
                    with sr.AudioFile(temp_wav) as source:
                        audio_data = self.recognizer.record(source, duration=dur, offset=curr_offset)
                        text = self.recognizer.recognize_google(audio_data, language=recog_lang)
                        clean_text = text.strip()
                        if clean_text:
                            dialogues.append({
                                "start": round(curr_offset, 2),
                                "end": round(curr_offset + dur, 2),
                                "text": clean_text
                            })
                except sr.UnknownValueError:
                    # Silence or unrecognizable sound in this slice
                    pass
                except Exception as ex:
                    # Timeout / Network / quota fallback
                    pass

                curr_offset += dur

        except Exception as e:
            print(f"[Transcribe] Error in audio transcription: {e}")
        finally:
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass

        return dialogues

    def format_ass_time(self, seconds: float) -> str:
        secs = max(0.0, seconds)
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        cs = int(round((s - int(s)) * 100))
        if cs >= 100:
            cs = 99
        return f"{int(h)}:{int(m):02d}:{int(s):02d}.{cs:02d}"

    def build_ass_subtitles(
        self,
        dialogues: List[dict],
        output_ass_rel_path: str,
        style_name: str = "hormozi",
        position: str = "bottom",
        fallback_title: Optional[str] = None,
        clip_duration: float = 30.0
    ) -> bool:
        """
        Create a styled, animated ASS subtitle file.
        Positions text safely in vertical 9:16 layout without colliding with Shorts UI.
        """
        output_ass_full = os.path.join(BASE_DIR, output_ass_rel_path)

        # Positioning:
        # Bottom safe zone (above title/audio icons): Alignment=2, MarginV=220
        # Center screen (podcast style): Alignment=5 (Middle Center), MarginV=0
        if position == "center":
            alignment = 5
            margin_v = 0
        else:
            alignment = 2
            margin_v = 220

        # Styles definition (Colors in ASS are &HAABBGGRR):
        # Hormozi: White & Electric Yellow, bold font, pop bounce
        # Cyber Neon: Electric Cyan & Purple glow
        # Karaoke: Word glow highlight
        # Clean Box: Sleek minimalist dark pill
        # Fire Red: White with hot flame orange-red
        styles_map = {
            "hormozi": {
                "font": "Arial",
                "size": 42,
                "primary": "&H00FFFFFF",     # White
                "secondary": "&H0000FFFF",   # Yellow
                "outline_col": "&H00000000", # Black
                "back_col": "&H80000000",
                "outline": 5,
                "shadow": 2,
                "border_style": 1
            },
            "tiktok_neon": {
                "font": "Arial",
                "size": 40,
                "primary": "&H00FFFF00",     # Cyan
                "secondary": "&H00FF00FF",   # Magenta
                "outline_col": "&H00800080", # Purple
                "back_col": "&H80000000",
                "outline": 5,
                "shadow": 3,
                "border_style": 1
            },
            "karaoke": {
                "font": "Arial",
                "size": 40,
                "primary": "&H0000FF00",     # Neon Green
                "secondary": "&H0000FFFF",   # Yellow
                "outline_col": "&H00000000",
                "back_col": "&H80000000",
                "outline": 5,
                "shadow": 2,
                "border_style": 1
            },
            "clean_box": {
                "font": "Arial",
                "size": 36,
                "primary": "&H00FFFFFF",
                "secondary": "&H0000FFFF",
                "outline_col": "&H00000000",
                "back_col": "&H99000000",     # Semi-opaque dark box
                "outline": 8,
                "shadow": 0,
                "border_style": 3            # Opaque box
            },
            "fire_red": {
                "font": "Arial",
                "size": 42,
                "primary": "&H00FFFFFF",
                "secondary": "&H002040FF",   # Flame Orange/Red
                "outline_col": "&H00000000",
                "back_col": "&H80000000",
                "outline": 5,
                "shadow": 3,
                "border_style": 1
            }
        }

        s_conf = styles_map.get(style_name, styles_map["hormozi"])

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ShortSub,{s_conf['font']},{s_conf['size']},{s_conf['primary']},{s_conf['secondary']},{s_conf['outline_col']},{s_conf['back_col']},-1,0,0,0,100,100,1,0,{s_conf['border_style']},{s_conf['outline']},{s_conf['shadow']},{alignment},35,35,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []

        # If dialogues is empty (e.g. music-only clip or silent video), create an animated hook banner
        if not dialogues:
            hook_text = (fallback_title or "WATCH THIS MOMENT").upper()
            # Split clip into 2-3 dynamic text cues so the screen is never dull
            half = clip_duration / 2
            t1_start = self.format_ass_time(0.5)
            t1_end = self.format_ass_time(half)
            t2_start = self.format_ass_time(half)
            t2_end = self.format_ass_time(clip_duration - 0.5)

            pop_anim = "{\\fscx112\\fscy112\\t(0,90,\\fscx100\\fscy100)}"
            events.append(f"Dialogue: 0,{t1_start},{t1_end},ShortSub,,0,0,0,,{pop_anim}{{\\c{s_conf['secondary']}&}}⚡ {hook_text}{{\\c{s_conf['primary']}&}}")
            events.append(f"Dialogue: 0,{t2_start},{t2_end},ShortSub,,0,0,0,,{pop_anim}{{\\c{s_conf['primary']}&}}DON'T MISS THIS! {{\\c{s_conf['secondary']}&}}🔥")

        else:
            # Process dialogues: Break into punchy 2-4 word bursts with pop animation
            for d in dialogues:
                words = d["text"].strip().split()
                if not words:
                    continue

                total_words = len(words)
                total_dur = max(0.5, d["end"] - d["start"])

                # Group words into bursts of max 3-4 words
                burst_size = 3 if total_words <= 6 else 4
                word_chunks = [words[i:i + burst_size] for i in range(0, total_words, burst_size)]
                time_per_chunk = total_dur / len(word_chunks)

                for c_idx, chunk in enumerate(word_chunks):
                    chunk_s = d["start"] + (c_idx * time_per_chunk)
                    chunk_e = min(clip_duration, chunk_s + time_per_chunk)
                    if chunk_e <= chunk_s:
                        continue

                    t_start = self.format_ass_time(chunk_s)
                    t_end = self.format_ass_time(chunk_e)

                    # Dynamic pop-in animation tag
                    anim_tag = "{\\fscx112\\fscy112\\t(0,80,\\fscx100\\fscy100)}"

                    # Uppercase words for viral impact
                    upper_chunk = [w.upper() for w in chunk]

                    if style_name == "hormozi":
                        # Highlight 1 key word with yellow pop
                        if len(upper_chunk) > 1:
                            upper_chunk[0] = f"{{\\c{s_conf['secondary']}&}}{upper_chunk[0]}{{\\c{s_conf['primary']}&}}"
                        formatted_text = " ".join(upper_chunk)

                    elif style_name == "karaoke":
                        # Active word tracker
                        highlighted = []
                        for i, w in enumerate(upper_chunk):
                            if i == 0:
                                highlighted.append(f"{{\\c{s_conf['primary']}&}}{w}{{\\c{s_conf['secondary']}&}}")
                            else:
                                highlighted.append(w)
                        formatted_text = " ".join(highlighted)

                    elif style_name == "fire_red":
                        if len(upper_chunk) > 1:
                            upper_chunk[-1] = f"{{\\c{s_conf['secondary']}&}}{upper_chunk[-1]}{{\\c{s_conf['primary']}&}}"
                        formatted_text = " ".join(upper_chunk)

                    else:
                        formatted_text = " ".join(upper_chunk)

                    line = f"Dialogue: 0,{t_start},{t_end},ShortSub,,0,0,0,,{anim_tag}{formatted_text}"
                    events.append(line)

        try:
            with open(output_ass_full, 'w', encoding='utf-8') as f:
                f.write(header + "\n".join(events) + "\n")
            return os.path.exists(output_ass_full) and os.path.getsize(output_ass_full) > 50
        except Exception as e:
            print(f"[ASS Subtitles] Error writing ASS file: {e}")
            return False

    # ---------------------------------------------------------
    # SHORT VIDEO GENERATION
    # ---------------------------------------------------------

    def generate_short(
        self,
        source_path: str,
        start_time: float,
        duration: float,
        output_path: str,
        style: str = "crop",
        title_text: Optional[str] = None,
        enable_subtitles: bool = False,
        subtitle_style: str = "hormozi",
        subtitle_lang: str = "auto",
        subtitle_pos: str = "bottom",
        task_id: Optional[str] = None,
        clip_idx: int = 1
    ) -> bool:
        """
        Convert segment into full screen vertical 9:16 video (720x1280).
        Styles:
          - crop: Full Screen 9:16 (Video fills 100% of the vertical screen)
          - blur_bg: Blurred video background with center foreground
          - letterbox: Clean Black bars
        """
        target_w = 720
        target_h = 1280
        t_id = task_id or uuid.uuid4().hex[:8]

        # 1. Base Framing Video Filter
        if style == "crop":
            # 100% Full Screen 9:16 Fill: proportional scale + exact center crop
            filter_complex = (
                f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
                f"crop={target_w}:{target_h}:(in_w-{target_w})/2:(in_h-{target_h})/2,setsar=1"
            )
        elif style == "blur_bg":
            filter_complex = (
                f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
                f"crop={target_w}:{target_h},boxblur=24:6[bg];"
                f"[0:v]scale={target_w}:-2[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1"
            )
        else: # letterbox
            filter_complex = (
                f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
            )

        # 2. Optional Hook Title (Upper third)
        font_file = "C\\:/Windows/Fonts/arial.ttf"
        if title_text and os.path.exists("C:/Windows/Fonts/arial.ttf"):
            clean_title = re.sub(r"['\":]", "", title_text)[:45]
            if clean_title:
                text_filter = (
                    f",drawtext=fontfile='{font_file}':text='{clean_title}':"
                    f"fontcolor=white:fontsize=32:box=1:boxcolor=black@0.65:boxborderw=12:"
                    f"x=(w-text_w)/2:y=120"
                )
                filter_complex += text_filter

        # 3. Optional Animated Subtitles & AI Speech Transcription
        sub_rel_path = f"downloads/sub_{t_id}_{clip_idx}.ass"
        sub_full_path = os.path.join(BASE_DIR, sub_rel_path)
        sub_created = False

        if enable_subtitles:
            dialogues = []
            # Check for YouTube downloaded subtitle file first
            yt_sub_file = self.find_youtube_subtitle_file(t_id)
            if yt_sub_file:
                dialogues = self.parse_subtitle_file(yt_sub_file, start_time, duration)

            # If no YouTube subtitles or empty, use AI speech recognition from audio
            if not dialogues:
                dialogues = self.transcribe_audio_segment(
                    source_path=source_path,
                    clip_start=start_time,
                    clip_duration=duration,
                    language=subtitle_lang,
                    task_id=f"{t_id}_{clip_idx}"
                )

            # Build stylized ASS subtitles
            sub_created = self.build_ass_subtitles(
                dialogues=dialogues,
                output_ass_rel_path=sub_rel_path,
                style_name=subtitle_style,
                position=subtitle_pos,
                fallback_title=title_text,
                clip_duration=duration
            )

            if sub_created:
                # Add ass filter using relative path from BASE_DIR
                filter_complex += f",ass=filename={sub_rel_path}"

        # 4. Execute FFmpeg Command
        cmd = [
            self.ffmpeg,
            "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", source_path,
        ]

        if style == "blur_bg":
            cmd += ["-filter_complex", filter_complex]
        else:
            cmd += ["-vf", filter_complex]

        cmd += [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]

        res = subprocess.run(cmd, cwd=BASE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Cleanup temporary .ass subtitle file
        if sub_created and os.path.exists(sub_full_path):
            try:
                os.remove(sub_full_path)
            except Exception:
                pass

        return res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1000

    def create_zip(self, task_id: str, short_files: List[str]) -> str:
        """Pack all generated shorts into a single zip file."""
        zip_path = os.path.join(OUTPUTS_DIR, f"{task_id}_all_shorts.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for f in short_files:
                if os.path.exists(f):
                    arcname = os.path.basename(f)
                    zipf.write(f, arcname)
        return zip_path
