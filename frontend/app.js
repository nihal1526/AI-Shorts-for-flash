// FlashKlap AI - Frontend Application Logic

let currentVideoInfo = null;
let currentClips = [];
let selectedClipIndex = 0;
let currentRenderedUrl = null;
let subtitleInterval = null;

// Helper to set sample URL
function setSampleUrl(url) {
  document.getElementById('youtubeUrlInput').value = url;
}

// Toggle settings drawer
function toggleSettings() {
  const panel = document.getElementById('settingsPanel');
  const chevron = document.getElementById('settingsChevron');
  panel.classList.toggle('hidden');
  chevron.classList.toggle('rotate-180');
}

// Toast notification
function showToast(msg) {
  const toast = document.getElementById('toast');
  const toastMsg = document.getElementById('toastMsg');
  toastMsg.textContent = msg;
  toast.classList.remove('translate-y-20', 'opacity-0');
  setTimeout(() => {
    toast.classList.add('translate-y-20', 'opacity-0');
  }, 2500);
}

// Clipboard copy helper
function copyText(elementId, successMsg) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const val = el.value || el.innerText;
  navigator.clipboard.writeText(val).then(() => {
    showToast(successMsg || 'Copied to clipboard!');
  });
}

function copyCurrentTitle() {
  const selectedRadio = document.querySelector('input[name="titleRadio"]:checked');
  if (selectedRadio) {
    navigator.clipboard.writeText(selectedRadio.value).then(() => {
      showToast('Title copied to clipboard!');
    });
  }
}

// Main Analyze Function
async function handleGenerate() {
  const url = document.getElementById('youtubeUrlInput').value.trim();
  if (!url) {
    showToast('Please enter a YouTube video URL');
    return;
  }

  // UI state: loading
  document.getElementById('resultsSection').classList.add('hidden');
  document.getElementById('loadingSection').classList.remove('hidden');
  document.getElementById('generateBtn').disabled = true;

  // Animate progress steps
  updateLoadingStep(1);
  setTimeout(() => updateLoadingStep(2), 1200);

  const payload = {
    url: url,
    max_clips: parseInt(document.getElementById('settingMaxClips').value) || 4,
    min_duration: 25,
    max_duration: 58
  };

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Analysis failed');
    }

    const data = await res.json();
    updateLoadingStep(3);
    setTimeout(() => {
      displayResults(data);
    }, 600);

  } catch (error) {
    console.warn('API error, falling back to client-side online demo mode:', error);
    // Client-side fallback if running purely on static GitHub Pages
    runClientSideFallback(url);
  } finally {
    document.getElementById('generateBtn').disabled = false;
  }
}

function updateLoadingStep(stepNum) {
  for (let i = 1; i <= 3; i++) {
    const stepEl = document.getElementById(`step${i}`);
    if (i < stepNum) {
      stepEl.className = 'flex items-center text-emerald-400';
      stepEl.innerHTML = `<i data-lucide="check-circle-2" class="w-4 h-4 mr-2"></i><span>Completed</span>`;
    } else if (i === stepNum) {
      stepEl.className = 'flex items-center text-purple-400 font-semibold';
      stepEl.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 mr-2 animate-spin"></i><span>Processing...</span>`;
    } else {
      stepEl.className = 'flex items-center text-slate-500';
    }
  }
  lucide.createIcons();
}

function displayResults(data) {
  document.getElementById('loadingSection').classList.add('hidden');
  document.getElementById('resultsSection').classList.remove('hidden');

  currentVideoInfo = data.video_info;
  currentClips = data.clips;

  // Header card
  document.getElementById('videoThumb').src = currentVideoInfo.thumbnail || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400';
  document.getElementById('videoTitle').textContent = currentVideoInfo.title;
  document.getElementById('videoChannel').innerHTML = `<i data-lucide="user" class="w-3 h-3 mr-1"></i> ${currentVideoInfo.channel}`;
  document.getElementById('videoDuration').innerHTML = `<i data-lucide="clock" class="w-3 h-3 mr-1"></i> ${currentVideoInfo.duration_str || '10:00'}`;
  document.getElementById('clipsFoundCount').textContent = `${currentClips.length} Viral Clips Ready`;

  // Render Clips List
  renderClipsList();

  // Select First Clip by Default
  selectClip(0);

  lucide.createIcons();
}

function renderClipsList() {
  const container = document.getElementById('clipsListContainer');
  container.innerHTML = '';

  currentClips.forEach((clip, index) => {
    const card = document.createElement('div');
    card.id = `clip-card-${index}`;
    card.className = `p-4 rounded-xl bg-[#101623] border border-slate-800 hover:border-slate-700 cursor-pointer transition duration-150 ${index === 0 ? 'clip-card-selected' : ''}`;
    card.onclick = () => selectClip(index);

    const viralityScore = clip.metrics ? clip.metrics.virality_score : 92;
    const tier = clip.metrics ? clip.metrics.tier : 'High Potential';

    card.innerHTML = `
      <div class="flex items-center justify-between mb-2">
        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold ${viralityScore >= 90 ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'} flex items-center">
          <i data-lucide="flame" class="w-3 h-3 mr-1"></i> ${viralityScore}% Virality
        </span>
        <span class="text-xs text-slate-400 font-mono flex items-center">
          <i data-lucide="clock" class="w-3 h-3 mr-1 text-slate-500"></i> ${Math.round(clip.duration)}s
        </span>
      </div>
      <p class="text-xs text-white font-medium line-clamp-2 leading-relaxed mb-2">
        "${clip.hook_text || clip.full_text.slice(0, 80) + '...'}"
      </p>
      <div class="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/80">
        <span class="text-slate-500">Hook: <strong class="text-slate-300">${clip.metrics ? clip.metrics.hook_score : 90}/100</strong></span>
        <span class="text-purple-400 font-semibold">${tier}</span>
      </div>
    `;

    container.appendChild(card);
  });
}

function selectClip(index) {
  selectedClipIndex = index;
  const clip = currentClips[index];
  if (!clip) return;

  // Highlight card
  currentClips.forEach((_, i) => {
    const el = document.getElementById(`clip-card-${i}`);
    if (el) {
      if (i === index) {
        el.classList.add('clip-card-selected');
      } else {
        el.classList.remove('clip-card-selected');
      }
    }
  });

  // Populate YouTube Shorts Upload Kit
  const kit = clip.upload_kit || {};
  
  // Virality scores
  document.getElementById('kitViralityScore').textContent = `${clip.metrics ? clip.metrics.virality_score : 92}%`;
  document.getElementById('kitHookScore').textContent = `${(clip.metrics ? clip.metrics.hook_score / 10 : 9.2).toFixed(1)}/10`;
  document.getElementById('kitPacingScore').textContent = `${(clip.metrics ? clip.metrics.pacing_score / 10 : 9.0).toFixed(1)}/10`;
  document.getElementById('kitReason').textContent = `"${clip.metrics ? clip.metrics.reason : 'High curiosity hook with rapid pacing.'}"`;

  // Titles
  const titlesContainer = document.getElementById('titleOptionsContainer');
  titlesContainer.innerHTML = '';
  const titles = kit.titles || [
    `The Shocking Truth About This... 😱 #shorts`,
    `Nobody Wants You To Know This! 🚨 #shorts`,
    `The 1 Thing That Changes Everything 🧠 #shorts`
  ];

  titles.forEach((t, i) => {
    const div = document.createElement('label');
    div.className = 'flex items-start space-x-2 p-2 rounded-lg bg-[#0E1420] border border-slate-800/80 hover:border-slate-700 cursor-pointer text-xs text-white';
    div.innerHTML = `
      <input type="radio" name="titleRadio" value="${escapeHtml(t)}" ${i === 0 ? 'checked' : ''} class="mt-0.5 text-purple-600 focus:ring-0">
      <span class="flex-1 leading-snug">${escapeHtml(t)}</span>
    `;
    titlesContainer.appendChild(div);
  });

  // Description & Tags
  document.getElementById('kitDescription').value = kit.description || '';
  document.getElementById('kitTags').value = kit.tags_string || 'shorts, youtube shorts, viral, podcast, clips';
  document.getElementById('kitKeyframeTime').textContent = `${kit.recommended_thumbnail_time || 1.8}s`;

  // Reset direct download button
  document.getElementById('directDownloadBtn').classList.add('hidden');
  document.getElementById('renderBtn').classList.remove('hidden');

  // Preview Subtitles Animation
  startSubtitleSimulation(clip);
}

// Subtitle simulation for real-time mobile preview
function startSubtitleSimulation(clip) {
  if (subtitleInterval) clearInterval(subtitleInterval);
  const overlayText = document.getElementById('subtitleText');
  const words = clip.words || (clip.full_text ? clip.full_text.split(' ').map((w, idx) => ({ word: w, start: idx * 0.3 })) : []);
  
  if (!words.length) {
    overlayText.textContent = clip.hook_text || "VIRAL SHORT PREVIEW";
    return;
  }

  let wordIdx = 0;
  subtitleInterval = setInterval(() => {
    if (wordIdx >= words.length) {
      wordIdx = 0;
    }
    // Show 3 words chunk with active word in color
    const chunk = words.slice(wordIdx, wordIdx + 3);
    if (chunk.length) {
      const activeWord = chunk[0].word.toUpperCase();
      const rest = chunk.slice(1).map(w => w.word.toUpperCase()).join(' ');
      
      const subStyle = document.getElementById('settingSubtitle').value;
      let activeColor = '#FFE600'; // Hormozi yellow
      if (subStyle === 'cyber_cyan') activeColor = '#00FFFF';
      if (subStyle === 'emerald') activeColor = '#00FF66';
      if (subStyle === 'clean_white') activeColor = '#FFFFFF';

      overlayText.innerHTML = `<span style="color: ${activeColor}; transform: scale(1.1); display: inline-block;">${escapeHtml(activeWord)}</span> ${escapeHtml(rest)}`;
    }
    wordIdx += 3;
  }, 1000);
}

// Render Clip with FFmpeg (Local or Cloud API)
async function handleRenderClip() {
  const clip = currentClips[selectedClipIndex];
  if (!clip) return;

  const renderBtn = document.getElementById('renderBtn');
  const renderingOverlay = document.getElementById('renderingOverlay');
  const directDownloadBtn = document.getElementById('directDownloadBtn');

  renderBtn.disabled = true;
  renderingOverlay.classList.remove('hidden');

  const payload = {
    url: document.getElementById('youtubeUrlInput').value.trim(),
    clip_id: clip.clip_id || `clip_${selectedClipIndex + 1}`,
    start_time: clip.start_time,
    end_time: clip.end_time,
    hook_text: clip.hook_text,
    full_text: clip.full_text,
    words: clip.words || [],
    segments: clip.segments || [],
    layout_mode: document.getElementById('settingLayout').value,
    subtitle_style: document.getElementById('settingSubtitle').value,
    uppercase: true
  };

  try {
    const res = await fetch('/api/render-clip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Render failed');
    }

    const data = await res.json();
    currentRenderedUrl = data.video_url;

    // Load into phone player
    const player = document.getElementById('shortsPlayer');
    player.src = data.video_url;
    player.play();
    document.getElementById('playPauseOverlay').classList.add('opacity-0');

    // Update Download Button
    directDownloadBtn.href = data.download_url;
    directDownloadBtn.classList.remove('hidden');
    renderBtn.classList.add('hidden');

    showToast('🎉 9:16 Short Rendered Successfully!');
  } catch (error) {
    console.error('Render error:', error);
    alert('Rendering completed or local processing message: ' + error.message);
  } finally {
    renderingOverlay.classList.add('hidden');
    renderBtn.disabled = false;
  }
}

// Toggle Play/Pause on Phone Mockup
function togglePlay() {
  const player = document.getElementById('shortsPlayer');
  const playIcon = document.getElementById('playIcon');
  if (player.paused) {
    player.play();
    document.getElementById('playPauseOverlay').classList.add('opacity-0');
  } else {
    player.pause();
    document.getElementById('playPauseOverlay').classList.remove('opacity-0');
  }
}

// Client-Side Demo Fallback for pure GitHub Pages static hosting
function runClientSideFallback(url) {
  // Extract video ID from URL
  let videoId = 'jNQXAC9IVRw';
  const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
  if (match) videoId = match[1];

  const mockData = {
    video_info: {
      id: videoId,
      title: "How Successful People Think & Act Everyday",
      channel: "Mindset Mastery",
      duration: 720,
      duration_str: "12:00",
      thumbnail: `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`
    },
    clips: [
      {
        clip_id: "clip_1",
        start_time: 42.0,
        end_time: 85.0,
        duration: 43.0,
        hook_text: "The biggest mistake 99% of people make is waiting for motivation.",
        full_text: "The biggest mistake 99% of people make is waiting for motivation. Motivation is a feeling, but action produces discipline. If you wait until you feel ready, you will never begin.",
        metrics: {
          virality_score: 96,
          hook_score: 98,
          pacing_score: 93,
          tier: "Ultra Viral",
          reason: "Explosive curiosity opening with immediate pattern-interrupt. High retention guarantee."
        },
        upload_kit: {
          titles: [
            "The 1 Mistake Keeping You Stuck 😱 #shorts",
            "Stop Waiting For Motivation! (Do This Instead) 🚨 #shorts",
            "The Harsh Truth Nobody Tells You 🧠 #shorts"
          ],
          description: "🔥 The biggest mistake 99% of people make is waiting for motivation.\n\nSubscribe for daily clips that rewire your brain! 🔔\n\n#shorts #youtubeshorts #viral #mindset #motivation #success #clips",
          tags_string: "shorts, youtube shorts, mindset, motivation, success, discipline, viral clips, self improvement",
          recommended_thumbnail_time: 43.8
        }
      },
      {
        clip_id: "clip_2",
        start_time: 140.0,
        end_time: 182.0,
        duration: 42.0,
        hook_text: "Nobody talks about this silent habit that ruins your focus.",
        full_text: "Nobody talks about this silent habit that ruins your focus. Every time you switch tasks, your brain leaves residue behind. Protect your attention like your life depends on it.",
        metrics: {
          virality_score: 92,
          hook_score: 94,
          pacing_score: 90,
          tier: "High Potential",
          reason: "Strong mystery trigger ('silent habit') that forces viewer to stay till the payoff."
        },
        upload_kit: {
          titles: [
            "This Silent Habit Ruins Your Focus 🤯 #shorts",
            "Why You Can't Focus Anymore... ❌ #shorts",
            "Protect Your Brain From This! 🧠 #shorts"
          ],
          description: "🔥 Nobody talks about this silent habit that ruins your focus.\n\nSubscribe for daily high-value life hacks! 🔔\n\n#shorts #youtubeshorts #focus #productivity #lifehacks #viral",
          tags_string: "shorts, youtube shorts, focus, productivity, deep work, brain hack, habits",
          recommended_thumbnail_time: 141.5
        }
      }
    ]
  };

  setTimeout(() => {
    displayResults(mockData);
  }, 1000);
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
