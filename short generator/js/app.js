// ShortCraft AI - Creator Studio Frontend Logic

let currentTab = 'youtube';
let selectedShortsCount = 3;
let selectedDuration = 30;
let activeTaskId = null;
let pollInterval = null;
let uploadedFile = null;

document.addEventListener('DOMContentLoaded', () => {
  initSegmentControls();
  initSampleButtons();
  initPasteButton();
  initFetchInfo();
  initSubtitleControls();
  initGenerateButton();
  initUploadDropzone();
});

// Tab Switcher
function switchTab(mode) {
  currentTab = mode;
  const tabYt = document.getElementById('tab-yt');
  const tabUpload = document.getElementById('tab-upload');
  const panelYt = document.getElementById('panel-youtube');
  const panelUpload = document.getElementById('panel-upload');

  if (mode === 'youtube') {
    tabYt.classList.add('active');
    tabUpload.classList.remove('active');
    panelYt.style.display = 'block';
    panelUpload.style.display = 'none';
  } else {
    tabUpload.classList.add('active');
    tabYt.classList.remove('active');
    panelUpload.style.display = 'block';
    panelYt.style.display = 'none';
  }
}

// Segmented Controls (Number of shorts & duration)
function initSegmentControls() {
  // Shorts Count
  const countButtons = document.querySelectorAll('#control-shorts-count .segment-btn');
  countButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      countButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedShortsCount = parseInt(btn.dataset.value);
    });
  });

  // Duration
  const durButtons = document.querySelectorAll('#control-duration .segment-btn');
  durButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      durButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedDuration = parseInt(btn.dataset.value);
    });
  });
}

// Quick Sample Buttons
function initSampleButtons() {
  const sampleChips = document.querySelectorAll('.chip-sample');
  const urlInput = document.getElementById('youtube-url');

  sampleChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const url = chip.dataset.url;
      urlInput.value = url;
      fetchVideoMetadata(url);
    });
  });
}

// Paste Button
function initPasteButton() {
  const pasteBtn = document.getElementById('btn-paste');
  const urlInput = document.getElementById('youtube-url');

  pasteBtn.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        urlInput.value = text.trim();
        fetchVideoMetadata(text.trim());
      }
    } catch (err) {
      urlInput.focus();
      alert("Please paste URL manually using Ctrl + V");
    }
  });
}

// Fetch Video Info Button & Auto Fetch
function initFetchInfo() {
  const fetchBtn = document.getElementById('btn-fetch-info');
  const urlInput = document.getElementById('youtube-url');

  fetchBtn.addEventListener('click', () => {
    const url = urlInput.value.trim();
    if (url) {
      fetchVideoMetadata(url);
    } else {
      alert("Kripya pehle YouTube video ka link yahan dalein!");
    }
  });

  // Trigger when URL changes and looks like a YouTube link
  urlInput.addEventListener('change', () => {
    const url = urlInput.value.trim();
    if (url.includes('youtube.com') || url.includes('youtu.be')) {
      fetchVideoMetadata(url);
    }
  });
}

async function fetchVideoMetadata(url) {
  const previewCard = document.getElementById('video-preview-card');
  const fetchBtn = document.getElementById('btn-fetch-info');
  
  fetchBtn.disabled = true;
  fetchBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Checking...`;

  try {
    const res = await fetch('/api/info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();

    if (data.success && data.info) {
      const info = data.info;
      document.getElementById('video-title').textContent = info.title;
      document.getElementById('video-author').textContent = info.author;
      document.getElementById('video-views').textContent = Number(info.views).toLocaleString();
      document.getElementById('video-duration').textContent = info.duration_formatted;
      document.getElementById('video-thumb').src = info.thumbnail;
      previewCard.style.display = 'flex';
    } else {
      console.warn("Could not fetch preview, will still process:", data.error);
    }
  } catch (err) {
    console.warn("Error fetching info:", err);
  } finally {
    fetchBtn.disabled = false;
    fetchBtn.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> Check`;
  }
}

// Subtitle & Speech Transcription Controls
function initSubtitleControls() {
  const toggleSubtitles = document.getElementById('toggle-subtitles');
  const optionsDrawer = document.getElementById('subtitle-options-drawer');
  const statusLabel = document.getElementById('subtitle-status-label');
  const previewBubble = document.getElementById('preview-bubble');
  const styleCards = document.querySelectorAll('.style-radio-card');

  if (!toggleSubtitles) return;

  // Toggle switch listener
  toggleSubtitles.addEventListener('change', () => {
    if (toggleSubtitles.checked) {
      optionsDrawer.style.display = 'block';
      statusLabel.textContent = 'ON';
      statusLabel.style.color = '#a855f7';
      statusLabel.style.fontWeight = '700';
    } else {
      optionsDrawer.style.display = 'none';
      statusLabel.textContent = 'OFF';
      statusLabel.style.color = '';
      statusLabel.style.fontWeight = '';
    }
  });

  // Style cards radio selector and preview bubble updater
  styleCards.forEach(card => {
    card.addEventListener('click', () => {
      styleCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      const radio = card.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;

      const styleVal = radio ? radio.value : 'hormozi';
      updateSubtitlePreview(styleVal);
    });
  });

  function updateSubtitlePreview(style) {
    if (!previewBubble) return;

    previewBubble.className = `preview-caption-bubble preview-${style}`;

    if (style === 'hormozi') {
      previewBubble.innerHTML = `<span class="highlight-word">THIS IS</span> VIRAL SHORTS AI`;
    } else if (style === 'tiktok_neon') {
      previewBubble.innerHTML = `VIRAL SHORTS AI`;
    } else if (style === 'karaoke') {
      previewBubble.innerHTML = `<span class="highlight-word">VIRAL</span> SHORTS AI`;
    } else if (style === 'clean_box') {
      previewBubble.innerHTML = `Viral Shorts AI`;
    } else if (style === 'fire_red') {
      previewBubble.innerHTML = `VIRAL SHORTS <span class="highlight-word">AI</span>`;
    }
  }
}

// Dropzone Upload
function initUploadDropzone() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const fileNameTag = document.getElementById('file-preview-name');

  if (!dropZone || !fileInput) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleSelectedFile(files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleSelectedFile(fileInput.files[0]);
    }
  });

  function handleSelectedFile(file) {
    uploadedFile = file;
    fileNameTag.textContent = `Selected: ${file.name} (${(file.size / (1024*1024)).toFixed(1)} MB)`;
    fileNameTag.style.display = 'inline-block';
  }
}

// Generate Shorts Handler
function initGenerateButton() {
  const generateBtn = document.getElementById('btn-generate');
  generateBtn.addEventListener('click', startGeneration);
}

async function startGeneration() {
  const generateBtn = document.getElementById('btn-generate');
  const progressContainer = document.getElementById('progress-container');
  const resultsSection = document.getElementById('results-section');
  const statusText = document.getElementById('progress-status-text');
  const percentText = document.getElementById('progress-percent');
  const progressBar = document.getElementById('progress-bar-fill');
  
  const style = document.getElementById('select-style').value;
  const overlayTitle = document.getElementById('toggle-hook-title').checked;

  // Subtitles settings
  const toggleSubtitles = document.getElementById('toggle-subtitles');
  const enableSubtitles = toggleSubtitles ? toggleSubtitles.checked : false;
  const selectedStyleRadio = document.querySelector('input[name="sub-style"]:checked');
  const subtitleStyle = selectedStyleRadio ? selectedStyleRadio.value : 'hormozi';
  const subtitleLang = document.getElementById('select-subtitle-lang') ? document.getElementById('select-subtitle-lang').value : 'auto';
  const subtitlePos = document.getElementById('select-subtitle-pos') ? document.getElementById('select-subtitle-pos').value : 'bottom';

  let requestBody;
  let isUpload = (currentTab === 'upload');

  if (!isUpload) {
    const url = document.getElementById('youtube-url').value.trim();
    if (!url) {
      alert("Kripya YouTube video ka URL link dalein!");
      document.getElementById('youtube-url').focus();
      return;
    }
    requestBody = {
      url: url,
      num_shorts: selectedShortsCount,
      duration: selectedDuration,
      style: style,
      overlay_title: overlayTitle,
      enable_subtitles: enableSubtitles,
      subtitle_style: subtitleStyle,
      subtitle_lang: subtitleLang,
      subtitle_pos: subtitlePos
    };
  } else {
    if (!uploadedFile) {
      alert("Kripya video file select karein!");
      return;
    }
  }

  // Reset & Show UI
  generateBtn.disabled = true;
  generateBtn.style.opacity = '0.6';
  resultsSection.style.display = 'none';
  progressContainer.style.display = 'block';
  progressBar.style.width = '5%';
  percentText.textContent = '5%';
  statusText.textContent = 'Pipeline start ho rahi hai...';

  // Highlight step chips
  updateStepChips(1);

  try {
    let res;
    if (!isUpload) {
      res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
    } else {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      formData.append('num_shorts', selectedShortsCount);
      formData.append('duration', selectedDuration);
      formData.append('style', style);
      formData.append('overlay_title', overlayTitle);
      formData.append('enable_subtitles', enableSubtitles);
      formData.append('subtitle_style', subtitleStyle);
      formData.append('subtitle_lang', subtitleLang);
      formData.append('subtitle_pos', subtitlePos);

      res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
    }

    const data = await res.json();
    if (!data.success || !data.task_id) {
      throw new Error(data.error || 'Server processing start nahi ho paya.');
    }

    activeTaskId = data.task_id;
    startProgressPolling(activeTaskId);

  } catch (err) {
    alert("Error: " + err.message);
    generateBtn.disabled = false;
    generateBtn.style.opacity = '1';
    progressContainer.style.display = 'none';
  }
}

function updateStepChips(step) {
  const chips = document.querySelectorAll('.step-chip');
  chips.forEach((c, i) => {
    if (i + 1 <= step) {
      c.classList.add('active');
    } else {
      c.classList.remove('active');
    }
  });
}

function startProgressPolling(taskId) {
  if (pollInterval) clearInterval(pollInterval);

  const statusText = document.getElementById('progress-status-text');
  const percentText = document.getElementById('progress-percent');
  const progressBar = document.getElementById('progress-bar-fill');
  const generateBtn = document.getElementById('btn-generate');

  pollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/progress/${taskId}`);
      const data = await res.json();

      if (data.status === 'processing' || data.status === 'queued') {
        const pct = data.progress || 10;
        progressBar.style.width = `${pct}%`;
        percentText.textContent = `${pct}%`;
        statusText.textContent = data.message || 'Processing video...';

        if (pct >= 40 && pct < 70) updateStepChips(2);
        if (pct >= 70) updateStepChips(3);
      } else if (data.status === 'completed') {
        clearInterval(pollInterval);
        progressBar.style.width = '100%';
        percentText.textContent = '100%';
        statusText.textContent = 'Sabhi Shorts taiyar ho gaye!';
        updateStepChips(3);

        generateBtn.disabled = false;
        generateBtn.style.opacity = '1';

        setTimeout(() => {
          renderGeneratedShorts(data.shorts, data.zip_url);
        }, 600);
      } else if (data.status === 'failed') {
        clearInterval(pollInterval);
        generateBtn.disabled = false;
        generateBtn.style.opacity = '1';
        alert("Processing me error aaya: " + (data.error || data.message));
        statusText.textContent = "Error: " + data.message;
      }
    } catch (e) {
      console.error("Progress poll error:", e);
    }
  }, 1000);
}

// Render Results Grid
function renderGeneratedShorts(shorts, zipUrl) {
  const resultsSection = document.getElementById('results-section');
  const grid = document.getElementById('shorts-grid');
  const zipBtn = document.getElementById('btn-download-all');

  grid.innerHTML = '';

  if (zipUrl) {
    zipBtn.href = zipUrl;
    zipBtn.style.display = 'inline-flex';
  } else {
    zipBtn.style.display = 'none';
  }

  shorts.forEach((short, idx) => {
    const card = document.createElement('div');
    card.className = 'short-card';
    
    // Format timestamp nicely
    const formatTime = (secs) => {
      const m = Math.floor(secs / 60);
      const s = Math.floor(secs % 60);
      return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    };

    const timeRange = `${formatTime(short.start)} - ${formatTime(short.end)}`;
    const subtitleBadge = short.subtitles_enabled 
      ? `<span class="subtitles-badge"><i class="fa-solid fa-closed-captioning"></i> AI Subtitles</span>` 
      : '';

    card.innerHTML = `
      <div class="video-wrapper">
        <span class="clip-index-badge">Short #${idx + 1}</span>
        <span class="viral-badge"><i class="fa-solid fa-fire"></i> ${short.viral_score}% Viral</span>
        ${subtitleBadge}
        <video 
          class="short-video-player" 
          controls 
          preload="metadata" 
          playsinline 
          src="${short.stream_url}"
        >
          Aapka browser video tag support nahi karta.
        </video>
      </div>
      <div class="short-card-body">
        <div class="d-drive-status-pill">
          <i class="fa-solid fa-circle-check text-green"></i> Auto-Saved to D:\\YouTube_Shorts
        </div>
        <h3 class="short-card-title">${short.label}</h3>
        <div class="short-card-meta">
          <span class="meta-item"><i class="fa-regular fa-clock"></i> ${short.duration}s</span>
          <span class="meta-item"><i class="fa-solid fa-scissors"></i> ${timeRange}</span>
          <span class="meta-item"><i class="fa-solid fa-hard-drive"></i> ${short.file_size}</span>
        </div>
        <div class="card-btn-group">
          <a href="${short.download_url}" download="${short.filename}" class="btn-download-short" onclick="handleShortDownload('${short.filename}')">
            <i class="fa-solid fa-arrow-down-to-line"></i> Download Short (${short.duration}s MP4)
          </a>
          <button type="button" class="btn-open-d-quick" title="D: Drive me yeh video dekhein" onclick="openDDriveFolder()">
            <i class="fa-solid fa-folder-open"></i> D: Drive
          </button>
        </div>
      </div>
    `;

    grid.appendChild(card);
  });

  resultsSection.style.display = 'block';

  // Smooth scroll down to results
  resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Open D: Drive Folder in Windows File Explorer
async function openDDriveFolder() {
  try {
    const res = await fetch('/api/open-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder: 'D:\\YouTube_Shorts' })
    });
    const data = await res.json();
    if (data.success) {
      showToast("📂 D: Drive folder File Explorer me open ho gaya!");
    } else {
      alert("Folder open karne me error aaya: " + (data.error || 'D drive not accessible'));
    }
  } catch (err) {
    console.error("Open folder error:", err);
  }
}

function handleShortDownload(filename) {
  showToast(`💾 "${filename}" download ho raha hai aur D: Drive me bhi saved hai!`);
}

// Simple Toast Notification
function showToast(message) {
  let toast = document.getElementById('app-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'app-toast';
    toast.className = 'app-toast';
    document.body.appendChild(toast);
  }
  toast.innerHTML = `<i class="fa-solid fa-circle-check text-green"></i> ${message}`;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 4000);
}
