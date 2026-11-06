---
title: FlashKlap AI - Free YouTube Shorts Generator
emoji: ✂️
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# ⚡ FlashKlap AI — Free AI YouTube Shorts Generator (Klap.app Alternative)

> Turn long YouTube videos (podcasts, speeches, interviews, educational videos) into ready-to-upload viral **YouTube Shorts, TikToks, and Reels** for 100% free. No subscriptions, no watermark, no limits.

Inspired by [Klap.app](https://klap.app/), FlashKlap automatically extracts the highest-converting moments, crops to 9:16 vertical format, adds dynamic animated subtitles (Alex Hormozi / MrBeast style), and provides a complete **YouTube Shorts Upload Kit** (viral titles, descriptions, hashtags, and SEO tags).

---

## 🌟 Features

- **🔗 Instant YouTube Ingestion**: Paste any YouTube link (or shortlink). FlashKlap fetches video details and transcript in seconds without downloading massive video files.
- **🔥 AI Virality Engine**: Analyzes speech pacing, emotional polarity, curiosity triggers ("mistake", "secret", "never", "why"), and retention potential to pick the top 3-5 viral clips.
- **📱 Smart 9:16 Vertical Reframing**:
  - **Blur Fill (Podcast / Landscape)**: Keeps the full original video centered with an aesthetically blurred background filling 9:16 (no faces or graphs cut off).
  - **Smart 9:16 Center Crop**: Full-bleed vertical crop filling the entire phone screen.
  - **Letterbox**: Clean black borders.
- **💬 Animated Dynamic Subtitles (ASS Substation Alpha)**:
  - **Viral Yellow (Hormozi style)**: Punchy uppercase font with active-word yellow highlights and black stroke.
  - **Neon Aqua (MrBeast style)**: Electric cyan word highlights.
  - **Electric Emerald**: High-energy green highlights.
  - **Minimalist White**: Clean modern look.
- **📦 Complete YouTube Shorts Upload Kit** (Everything needed when uploading to YouTube Shorts):
  - **3 High-CTR Viral Titles**: Curiosity gap, urgent warning, and question hooks.
  - **Shorts-Optimized Description**: Includes opening hook line, call-to-action, timestamps, and trending hashtags (`#shorts #viral #youtubeshorts #podcast`).
  - **YouTube Studio SEO Tags**: 15+ comma-separated tags ready to copy and paste directly into YouTube Studio.
  - **Thumbnail Keyframe Timestamp**: Pinpoints the ideal visual moment to capture the viewer's attention.
  - **Virality Scorecard**: Detailed breakdown of Hook strength, Pacing, and predicted Audience Retention.
- **⚡ 1-Click Fast Render & Download**: Fast section cuts and FFmpeg rendering producing crisp 1080x1920 MP4 files ready to upload.

---

## 🚀 How to Run Locally

### 1. Prerequisites
- Python 3.10+
- FFmpeg installed and available in PATH (already installed on your machine)

### 2. Quick Start
Double-click `run.py` or run:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python run.py
```

Your browser will automatically open to `http://localhost:8000`.

---

## 🌐 How to Host on GitHub & Use It ONLINE for FREE

You can host this project on GitHub and run it online for free using any of these 3 methods:

### Method 1: Hugging Face Spaces (Recommended — 100% Free Forever)
Hugging Face offers free Docker containers with CPU/GPU and FFmpeg:
1. Create a free account at [huggingface.co](https://huggingface.co/).
2. Click **New Space** -> Name it `flashklap` -> Select **Docker** as Space SDK.
3. Under **Repository Type**, choose **Public**.
4. In Space Settings, link your GitHub repository (or push this repo directly to Hugging Face).
5. Hugging Face will automatically build the included `Dockerfile` and give you a permanent online web link:
   ```
   https://<your-username>-flashklap.hf.space
   ```
   You can access and use it from anywhere on your phone, laptop, or tablet!

---

### Method 2: GitHub Codespaces (One-Click Online Browser Environment)
GitHub provides **60 hours of free cloud computing every month** on every GitHub account:
1. Push this project to your GitHub repository (see steps below).
2. On your GitHub repo page, click the green **`<> Code`** button.
3. Switch to the **Codespaces** tab and click **Create codespace on main**.
4. GitHub opens a full VS Code editor directly inside your browser. The included `.devcontainer/devcontainer.json` will automatically configure FFmpeg and Python.
5. In the terminal, type:
   ```bash
   python run.py
   ```
6. A popup will appear: *"Your application running on port 8000 is available."* Click **Open in Browser** to use it online!

---

### Method 3: Free Cloud Hosting (Render / Railway / Koyeb)
- **Render.com**:
  1. Go to [render.com](https://render.com/) and connect your GitHub account.
  2. Click **New +** -> **Web Service**.
  3. Select your FlashKlap GitHub repository.
  4. Render will detect the included `Dockerfile` and `render.yaml`.
  5. Select the **Free** tier and click **Deploy**.
  6. You get a free live URL: `https://flashklap.onrender.com`.

---

## 📤 How to Push This Project to Your GitHub Account

Run these commands in PowerShell or Terminal in this folder:

```bash
# 1. Initialize git repository
git init

# 2. Add all files
git add .

# 3. Commit
git commit -m "Initial commit: FlashKlap AI free YouTube Shorts generator"

# 4. Set branch to main
git branch -M main

# 5. Connect to your GitHub repository (replace with your repo URL)
git remote add origin https://github.com/<YOUR-USERNAME>/<YOUR-REPO-NAME>.git

# 6. Push to GitHub
git push -u origin main
```

---

## 🛠️ Project Structure

```
├── backend/
│   ├── app.py                 # FastAPI backend & API endpoints
│   ├── config.py              # Configuration & subtitle style presets
│   ├── youtube_downloader.py  # yt-dlp metadata & fast section downloader
│   ├── virality_engine.py     # AI hook analysis & virality scoring
│   ├── metadata_generator.py  # High-CTR titles, descriptions & tags
│   ├── subtitle_generator.py  # ASS dynamic animated subtitles (Hormozi style)
│   └── video_processor.py     # FFmpeg 9:16 vertical video rendering
├── frontend/
│   ├── index.html             # Klap-inspired dark UI with phone mockup
│   ├── app.js                 # Frontend interactivity & real-time preview
│   └── styles.css             # Subtitle stroke & custom styling
├── storage/
│   ├── downloads/             # Video clips cache
│   ├── rendered/              # Exported 1080x1920 MP4 Shorts
│   └── temp/                  # Temp subtitle files
├── .devcontainer/             # GitHub Codespaces online configuration
├── .github/workflows/         # GitHub Actions CI pipeline
├── Dockerfile                 # Cloud container for Hugging Face / Render
├── render.yaml                # Render 1-click cloud config
├── requirements.txt           # Python dependencies
├── run.py                     # One-click launch script
└── README.md                  # Project documentation
```

---

## 📄 License
MIT License. Free to use, modify, and distribute.
