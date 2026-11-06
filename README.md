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

### Method 1: GitHub Pages (Direct Free Website on GitHub)
Your repository is pre-configured with automated GitHub Pages deployment:
1. Open your repository: **[https://github.com/nihal1526/AI-Shorts-for-flash](https://github.com/nihal1526/AI-Shorts-for-flash)**
2. Click on **Settings** (tab at the top) -> In the left sidebar, click **Pages**.
3. Under **Build and deployment**:
   - **Source**: Select **GitHub Actions** (the included `.github/workflows/pages.yml` will deploy it automatically), OR select **Deploy from a branch** -> branch **`main`** -> folder **`/ (root)`** -> click **Save**.
4. In ~60 seconds, your site will be live at:
   ```
   https://nihal1526.github.io/AI-Shorts-for-flash/
   ```
   Anyone can visit this URL on mobile or desktop, paste any YouTube link, and extract viral clips, titles, descriptions, and tags!

---

### Method 2: GitHub Codespaces (Full Cloud Environment with FFmpeg & Python)
GitHub provides **60 hours of free cloud computing every month** on every account:
1. On your GitHub repo page, click the green **`<> Code`** button.
2. Switch to the **Codespaces** tab and click **Create codespace on main**.
3. GitHub opens a cloud VS Code environment in your browser. The included `.devcontainer/devcontainer.json` will automatically configure FFmpeg and Python.
4. In the terminal, type:
   ```bash
   python run.py
   ```
5. Click **Open in Browser** when the port 8000 popup appears to use the full application online!

---

### Method 3: Hugging Face Spaces (Permanent Free Cloud Docker Container)
Hugging Face offers free Docker containers with CPU/GPU and FFmpeg:
1. Create a free account at [huggingface.co](https://huggingface.co/).
2. Click **New Space** -> Name it `ai-shorts-for-flash` -> Select **Docker** as Space SDK.
3. Under Settings, connect your GitHub repo `nihal1526/AI-Shorts-for-flash`.
4. Hugging Face automatically builds the included `Dockerfile` and gives you a permanent online web link:
   ```
   https://nihal1526-ai-shorts-for-flash.hf.space
   ```

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

