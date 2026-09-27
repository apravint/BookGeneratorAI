// State management
let currentJobId = null;
let pollTimer = null;
let activeChapterNum = 0;
let generatedChapters = {};

const PRESETS = {
  historical: {
    title: "சோழர் பேரரசின் ரகசியம்",
    concept: "11-ஆம் நூற்றாண்டில் சோழப் பேரரசின் கடற்படைப் படையெடுப்பு, அரசதந்திர சூழ்ச்சிகள் மற்றும் ஒரு இளம் தளபதியின் வீரக் காவியம்.",
    genre: "tamil_historical",
    author: "பிரவின் தமிழன்"
  },
  thirukkural: {
    title: "திருக்குறள் மேலாண்மை தத்துவம்",
    concept: "திருக்குறளின் பொருட்பால் அடிப்படையிலான தலைமைத்துவம், ஆட்சிமுறை, நிதி மேலாண்மை மற்றும் மனிதவள வழிகாட்டி.",
    genre: "tamil_thirukkural",
    author: "பிரவின் தமிழன்"
  },
  kavithai: {
    title: "காதலும் தத்துவமும்: கவிதைத் தொகுப்பு",
    concept: "இயற்கை, காதல், வாழ்வியல் தத்துவங்கள் மற்றும் சமூக சீர்திருத்தக் கருத்துகள் கொண்ட நவீன தமிழ்க் கவிதைகள்.",
    genre: "tamil_kavithai",
    author: "பிரவின் தமிழன்"
  },
  fiction: {
    title: "அலைகளின் ஓசை",
    concept: "கடலோரக் கிராமம் ஒன்றில் நடக்கும் உணர்வுப்பூர்வமான வாழ்க்கை, காதல் மற்றும் மனித சமூகப் போராட்டங்களின் காவியம்.",
    genre: "tamil_fiction",
    author: "பிரவின் தமிழன்"
  }
};

function applyPreset(key) {
  const p = PRESETS[key];
  if (!p) return;

  document.getElementById("book-title").value = p.title;
  document.getElementById("book-concept").value = p.concept;
  document.getElementById("author-name").value = p.author;
  document.getElementById("book-genre").value = p.genre;
  document.getElementById("book-language").value = "tamil";
  
  // Highlight card
  document.querySelectorAll(".preset-card").forEach(c => c.style.borderColor = "var(--bg-card-border)");
  const card = document.querySelector(`.preset-card[data-preset="${key}"]`);
  if (card) card.style.borderColor = "var(--primary-gold)";

  // Scroll to form
  document.querySelector(".form-card").scrollIntoView({ behavior: "smooth" });
}

function toggleProviderSettings() {
  const provider = document.getElementById("ai-provider").value;
  const modelInput = document.getElementById("model-name");
  
  if (provider === "ollama") {
    modelInput.value = "deepseek-r1:latest";
  } else if (provider === "gemini") {
    modelInput.value = "gemini-1.5-flash";
  } else if (provider === "openai") {
    modelInput.value = "gpt-4o";
  } else if (provider === "anthropic") {
    modelInput.value = "claude-3-5-sonnet-20240620";
  }
}

async function handleGenerate(e) {
  e.preventDefault();

  const title = document.getElementById("book-title").value.trim();
  const concept = document.getElementById("book-concept").value.trim();
  const author = document.getElementById("author-name").value.trim();
  const language = document.getElementById("book-language").value;
  const genre = document.getElementById("book-genre").value;
  const provider = document.getElementById("ai-provider").value;
  const model = document.getElementById("model-name").value.trim();

  if (!title) {
    alert("தயவுசெய்து புத்தகத்தின் தலைப்பை உள்ளிடவும்.");
    return;
  }

  // UI state update
  document.getElementById("btn-generate").disabled = true;
  document.getElementById("btn-generate").innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> உருவாக்கம் தொடங்குகிறது...';
  document.getElementById("engine-status").className = "status-pill status-running";
  document.getElementById("engine-status").textContent = "இயங்குகிறது (Generating...)";
  
  document.getElementById("progress-box").classList.remove("hidden");
  document.getElementById("progress-message").textContent = "AI ஏஜென்ட்கள் பணியைத் தொடங்குகின்றன...";
  document.getElementById("progress-fill").style.width = "5%";
  document.getElementById("progress-percent").textContent = "5%";

  resetPipelineTracker();

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, concept, author, language, genre, provider, model })
    });

    const data = await res.json();
    if (data.status === "started" || data.status === "ok") {
      currentJobId = data.job_id || "active";
      startPolling();
    } else {
      alert("பிழை: " + (data.error || "புத்தகம் உருவாக்கத் தொடங்குவதில் சிக்கல்."));
      resetFormBtn();
    }
  } catch (err) {
    console.error("API error:", err);
    alert("சேவையகத்துடன் இணைப்பதில் பிழை ஏற்பட்டது.");
    resetFormBtn();
  }
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(checkStatus, 3000);
  checkStatus();
}

async function checkStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();

    updatePipelineUI(data);

    if (data.chapters && data.chapters.length > 0) {
      updateChapterTabs(data.chapters);
    }

    if (data.status === "completed") {
      clearInterval(pollTimer);
      document.getElementById("engine-status").className = "status-pill status-ready";
      document.getElementById("engine-status").textContent = "நிறைவடைந்தது (Completed)";
      document.getElementById("progress-message").textContent = "🎉 புத்தகம் வெற்றிகரமாக உருவாக்கப்பட்டுவிட்டது!";
      document.getElementById("progress-fill").style.width = "100%";
      document.getElementById("progress-percent").textContent = "100%";
      document.getElementById("btn-download-docx").disabled = false;
      resetFormBtn();
    } else if (data.status === "failed") {
      clearInterval(pollTimer);
      document.getElementById("engine-status").className = "status-pill";
      document.getElementById("engine-status").textContent = "தோல்வி (Failed)";
      document.getElementById("progress-message").textContent = "⚠️ பிழை: " + (data.error || "உருவாக்கம் தடைபட்டது.");
      resetFormBtn();
    }
  } catch (err) {
    console.error("Polling status error:", err);
  }
}

function updatePipelineUI(data) {
  const phase = data.phase || "world";
  const progressPercent = data.progress_percent || 10;
  
  document.getElementById("progress-message").textContent = data.message || "ஏஜென்ட்கள் செயல்படுகின்றன...";
  document.getElementById("progress-fill").style.width = progressPercent + "%";
  document.getElementById("progress-percent").textContent = progressPercent + "%";

  const nodes = {
    world: document.getElementById("node-world"),
    char: document.getElementById("node-char"),
    outline: document.getElementById("node-outline"),
    draft: document.getElementById("node-draft"),
    docx: document.getElementById("node-docx")
  };

  // Reset classes
  Object.values(nodes).forEach(n => {
    if (n) n.className = "step-node";
  });

  if (phase === "world") {
    nodes.world.className = "step-node active";
  } else if (phase === "char") {
    nodes.world.className = "step-node done";
    nodes.char.className = "step-node active";
  } else if (phase === "outline") {
    nodes.world.className = "step-node done";
    nodes.char.className = "step-node done";
    nodes.outline.className = "step-node active";
  } else if (phase === "draft") {
    nodes.world.className = "step-node done";
    nodes.char.className = "step-node done";
    nodes.outline.className = "step-node done";
    nodes.draft.className = "step-node active";
  } else if (phase === "docx" || phase === "completed") {
    nodes.world.className = "step-node done";
    nodes.char.className = "step-node done";
    nodes.outline.className = "step-node done";
    nodes.draft.className = "step-node done";
    nodes.docx.className = "step-node done";
  }
}

function updateChapterTabs(chapters) {
  const tabsContainer = document.getElementById("chapter-tabs");
  tabsContainer.innerHTML = "";

  chapters.forEach((chap, idx) => {
    const num = idx + 1;
    const btn = document.createElement("button");
    btn.className = `tab-btn ${activeChapterNum === num ? "active" : ""}`;
    btn.textContent = `அத்தியாயம் ${num}`;
    btn.onclick = () => switchChapter(num);
    tabsContainer.appendChild(btn);
  });

  if (activeChapterNum === 0 && chapters.length > 0) {
    switchChapter(1);
  }
}

async function switchChapter(num) {
  activeChapterNum = num;
  
  // Highlight tab
  document.querySelectorAll(".tab-btn").forEach((t, i) => {
    if (i + 1 === num) t.classList.add("active");
    else t.classList.remove("active");
  });

  const contentBox = document.getElementById("manuscript-content");
  contentBox.innerHTML = `<div class="empty-state"><i class="fa-solid fa-spinner fa-spin empty-icon"></i><h4>அத்தியாயம் ${num} ஏற்றப்படுகிறது...</h4></div>`;

  try {
    const res = await fetch(`/api/chapters/${num}`);
    const data = await res.json();

    if (data.content) {
      contentBox.innerHTML = renderMarkdown(data.content);
    } else {
      contentBox.innerHTML = `<div class="empty-state"><p>அத்தியாயம் ${num} இன்னும் உருவாக்கப்படவில்லை.</p></div>`;
    }
  } catch (err) {
    contentBox.innerHTML = `<div class="empty-state"><p>உள்ளடக்கத்தை ஏற்றுவதில் பிழை ஏற்பட்டது.</p></div>`;
  }
}

function renderMarkdown(md) {
  let html = md
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '### $1')
    .replace(/\*\*(.* vast?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.* vast?)\*/gim, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>');

  return `<div class="md-rendered"><p>${html}</p></div>`;
}

function downloadDocx() {
  window.location.href = "/api/download";
}

function resetFormBtn() {
  const btn = document.getElementById("btn-generate");
  btn.disabled = false;
  btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> புத்தகம் உருவாக்கத் தொடங்கு (Start AI Generation)';
}

function resetPipelineTracker() {
  document.querySelectorAll(".step-node").forEach(n => n.className = "step-node");
}
