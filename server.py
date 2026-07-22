from flask import Flask, render_template_string, request, redirect, url_for, send_file, jsonify
import database
import os
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "js-local-secret-2024")


def get_audio_filename(path):
    if not path:
        return ""
    return path.replace("\\", "/").split("/")[-1]


def generate_insights(history):
    if not history:
        return "Analyzing style...", 0
    text = " ".join([h['transcript'] for h in history]).lower()
    words = text.split()
    if not words:
        return "Analyzing style...", 0
    fillers = ['um', 'uh', 'like', 'you know', 'so', 'basically', 'actually']
    filler_count = sum(1 for w in words if w in fillers)
    avg_len = len(words) / len(history)
    score = int(
        min(100, max(0, 100 - (filler_count / max(len(words), 1)) * 400)))
    if filler_count > len(words) * 0.05:
        return "Conversational", score
    elif avg_len > 25:
        return "Expressive", score
    elif avg_len < 6:
        return "Concise", score
    else:
        return "Fluent", score


HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="{{ theme }}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>JustSay Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root {
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --trans: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  --r-xl: 24px;
  --r-lg: 16px;
  --r-md: 12px;
}

[data-theme=dark] {
  --bg: #09090b;
  --surface: rgba(24, 24, 27, 0.65);
  --surface-hover: rgba(39, 39, 42, 0.85);
  --border: rgba(255,255,255,0.08);
  --border-strong: rgba(255,255,255,0.15);
  --text: #fafafa;
  --text-muted: #a1a1aa;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --accent-glow: rgba(59, 130, 246, 0.2);
  --danger: #ef4444;
  --shadow: 0 10px 40px rgba(0,0,0,0.8);
  --input-bg: rgba(255,255,255,0.03);
}

[data-theme=light] {
  --bg: #ffffff;
  --surface: rgba(244, 244, 245, 0.7);
  --surface-hover: rgba(228, 228, 231, 0.95);
  --border: rgba(0,0,0,0.08);
  --border-strong: rgba(0,0,0,0.15);
  --text: #09090b;
  --text-muted: #71717a;
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --accent-glow: rgba(37, 99, 235, 0.15);
  --danger: #dc2626;
  --shadow: 0 10px 40px rgba(0,0,0,0.06);
  --input-bg: rgba(0,0,0,0.02);
}

body {
  font-family: var(--font-sans);
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
  position: relative;
}

/* Subtler Animated Gradient Mesh Background */
.bg-mesh {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  z-index: -1;
  background-image: 
    radial-gradient(circle at 10% 50%, var(--accent-glow), transparent 40%),
    radial-gradient(circle at 90% 20%, rgba(139, 92, 246, 0.08), transparent 40%);
  filter: blur(80px);
  animation: meshAnim 20s infinite alternate;
}
@keyframes meshAnim {
  0% { transform: scale(1); }
  100% { transform: scale(1.05); }
}

/* APP LAYOUT */
.app-container { display: flex; height: 100vh; width: 100vw; }

/* SIDEBAR */
.sidebar {
  width: 260px;
  background: transparent;
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  z-index: 10;
  border-right: 1px solid var(--border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 50px;
  padding: 0 12px;
}
.brand-icon { width: 36px; height: 36px; background: linear-gradient(135deg, var(--accent), #8b5cf6); color: #fff; border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px var(--accent-glow); }
.brand-text { font-size: 1.25rem; font-weight: 700; letter-spacing: -0.5px; }

.nav-item {
  padding: 12px 16px;
  border-radius: var(--r-md);
  margin-bottom: 6px;
  color: var(--text-muted);
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  transition: var(--trans);
  display: flex;
  align-items: center;
  gap: 12px;
  user-select: none;
}
.nav-item svg { width: 18px; height: 18px; opacity: 0.7; }
.nav-item:hover { background: var(--surface-hover); color: var(--text); }
.nav-item.active { background: var(--surface); color: var(--text); border: 1px solid var(--border); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.nav-item.active svg { opacity: 1; color: var(--accent); }
.sidebar-bottom { margin-top: auto; }

.version-tag {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-align: center;
  margin-top: 16px;
  opacity: 0.6;
  letter-spacing: 0.5px;
}

/* MAIN CONTENT */
.main-content {
  flex: 1;
  padding: 50px 70px;
  overflow-y: auto;
  scroll-behavior: smooth;
  background: linear-gradient(to right, rgba(0,0,0,0.2), transparent);
}
.header-title { font-size: 3rem; font-weight: 600; letter-spacing: -1px; margin-bottom: 10px; }
.header-sub { font-size: 1.1rem; color: var(--text-muted); margin-bottom: 40px; font-weight: 400; }

/* CARDS */
.card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 40px; }
.card {
  background: var(--surface);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--border);
  border-radius: var(--r-xl);
  padding: 30px;
  transition: var(--trans);
  position: relative;
  overflow: hidden;
}
.card:hover { transform: translateY(-2px); border-color: var(--border-strong); box-shadow: var(--shadow); }
.card-title { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 12px; }
.card-value { font-size: 3rem; font-weight: 600; letter-spacing: -1px; line-height: 1.1; margin-bottom: 8px; }
.card-desc { font-size: 0.9rem; color: var(--text-muted); line-height: 1.5; }

/* FORMS & BUTTONS */
.btn {
  background: var(--text);
  color: var(--bg);
  border: none;
  padding: 12px 24px;
  border-radius: var(--r-md);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--trans);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}
.btn:hover { background: var(--text-muted); transform: scale(1.02); }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { background: var(--accent-hover); box-shadow: 0 0 15px var(--accent-glow); }
.btn-danger { background: rgba(239, 68, 68, 0.1); color: var(--danger); border: 1px solid rgba(239, 68, 68, 0.2); }
.btn-danger:hover { background: var(--danger); color: #fff; }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
.btn-outline:hover { background: var(--surface-hover); border-color: var(--border-strong); }

input, select {
  background: var(--input-bg);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 14px 18px;
  border-radius: var(--r-md);
  font-size: 0.95rem;
  width: 100%;
  transition: var(--trans);
  outline: none;
  font-family: var(--font-sans);
}
input:focus, select:focus { border-color: var(--accent); background: var(--surface); box-shadow: 0 0 0 3px var(--accent-glow); }
.form-group { margin-bottom: 20px; }
.form-label { display: block; font-weight: 500; margin-bottom: 8px; font-size: 0.9rem; color: var(--text-muted); }
.form-row { display: flex; gap: 12px; align-items: center; }

/* SECTIONS */
.section { display: none; opacity: 0; animation: fadeUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.section.active { display: block; }
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

/* TABLES */
.table-wrap { overflow-x: auto; margin-top: 5px; }
table { width: 100%; border-collapse: separate; border-spacing: 0; }
th { text-align: left; color: var(--text-muted); font-size: 0.8rem; font-weight: 600; text-transform: uppercase; padding: 14px 20px; border-bottom: 1px solid var(--border); letter-spacing: 0.5px; }
td { padding: 16px 20px; border-bottom: 1px solid var(--border); font-size: 0.95rem; font-weight: 400; }
tr:last-child td { border-bottom: none; }
tr { transition: var(--trans); }
tr:hover td { background: var(--surface-hover); }

/* TAGS & SHORTCUTS */
.tags { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
.tag {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 6px 14px;
  border-radius: var(--r-md);
  font-size: 0.85rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}
.tag a { color: var(--text-muted); text-decoration: none; font-size: 1.1rem; line-height: 1; transition: var(--trans); }
.tag a:hover { color: var(--danger); }

.shortcut-box {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 20px;
  border-radius: var(--r-lg);
  margin-bottom: 16px;
  transition: var(--trans);
}
.shortcut-box:hover { border-color: var(--border-strong); }
.shortcut-keys { display: inline-flex; gap: 4px; }
.shortcut-keys kbd {
  background: var(--text);
  color: var(--bg);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  display: inline-block;
  text-transform: uppercase;
}

/* WISPR FLOW INSPIRED ONBOARDING */
.onboard-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  width: 100vw;
}
.onboard-card {
  background: var(--surface);
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  border: 1px solid var(--border-strong);
  border-radius: 32px;
  padding: 60px 50px;
  width: 100%;
  max-width: 540px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  text-align: center;
  position: relative;
  overflow: hidden;
}
.onboard-step { display: none; opacity: 0; animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.onboard-step.active { display: block; }
.onboard-icon { margin: 0 auto 30px; width: 64px; height: 64px; background: linear-gradient(135deg, var(--accent), #8b5cf6); color: #fff; border-radius: 20px; display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 25px var(--accent-glow); }

/* STYLE PICKER CARDS */
.style-picker {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 30px 0;
  text-align: left;
}
.style-card {
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 16px;
  cursor: pointer;
  transition: var(--trans);
  background: var(--input-bg);
}
.style-card:hover { border-color: var(--border-strong); background: var(--surface-hover); }
.style-card.selected { border-color: var(--accent); background: var(--accent-glow); box-shadow: 0 0 0 1px var(--accent); }
.style-title { font-size: 1rem; font-weight: 600; margin-bottom: 4px; }
.style-desc { font-size: 0.8rem; color: var(--text-muted); }

/* RECORDING INDICATOR */
.recording-active {
  background: var(--danger) !important;
  color: white !important;
  animation: pulseRed 1.5s infinite;
}
@keyframes pulseRed {
  0% { box-shadow: 0 0 0 0 rgba(239,68,68, 0.4); }
  70% { box-shadow: 0 0 0 8px rgba(239,68,68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239,68,68, 0); }
}
</style>
</head>
<body>
<div class="bg-mesh"></div>

{% if not settings.onboarded %}
<!-- ONBOARDING FLOW -->
<div class="onboard-container">
  <div class="onboard-card">
    <form id="onboard-form" action="/complete_onboarding" method="POST">
      
      <!-- STEP 1: Welcome -->
      <div class="onboard-step active" id="step-1">
        <div class="onboard-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:32px;height:32px;"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v1a7 7 0 0 1-14 0v-1M12 19v3M8 22h8"/></svg>
        </div>
        <h1 class="header-title" style="font-size:2.2rem;margin-bottom:10px;">Meet JustSay</h1>
        <p class="header-sub">Your brilliant, fully-local AI voice assistant. Let's get things set up perfectly.</p>
        <button type="button" class="btn btn-primary" style="width:100%;margin-top:20px;font-size:1rem;padding:14px;border-radius:24px;" onclick="nextStep(2)">Get Started</button>
      </div>

      <!-- STEP 2: Shortcuts -->
      <div class="onboard-step" id="step-2">
        <h1 class="header-title" style="font-size:1.8rem;margin-bottom:10px;">Set Your Triggers</h1>
        <p class="header-sub" style="margin-bottom:24px;">How do you want to start dictating?</p>
        
        <div class="form-group" style="text-align:left;">
          <label class="form-label">Push-to-Talk (Hold & Speak)</label>
          <div style="display:flex;gap:10px;align-items:center;">
            <input type="hidden" name="hotkey_ptt" id="ob_ptt_input" value="ctrl+windows">
            <div id="ob_ptt_input_display" class="shortcut-keys" style="flex:1;"><kbd>CTRL</kbd><kbd>WINDOWS</kbd></div>
            <button type="button" class="btn btn-outline" style="border-radius:24px" onclick="startRecording(this, 'ob_ptt_input')">Record</button>
          </div>
        </div>

        <div class="form-group" style="text-align:left;margin-top:24px;">
          <label class="form-label">Toggle (Tap to Start/Stop)</label>
          <div style="display:flex;gap:10px;align-items:center;">
            <input type="hidden" name="hotkey_toggle" id="ob_toggle_input" value="ctrl+windows+space">
            <div id="ob_toggle_input_display" class="shortcut-keys" style="flex:1;"><kbd>CTRL</kbd><kbd>WINDOWS</kbd><kbd>SPACE</kbd></div>
            <button type="button" class="btn btn-outline" style="border-radius:24px" onclick="startRecording(this, 'ob_toggle_input')">Record</button>
          </div>
        </div>

        <div style="display:flex;gap:12px;margin-top:30px;">
          <button type="button" class="btn btn-outline" style="flex:1;padding:14px;border-radius:24px;" onclick="nextStep(1)">Back</button>
          <button type="button" class="btn btn-primary" style="flex:1;padding:14px;border-radius:24px;" onclick="nextStep(3)">Continue</button>
        </div>
      </div>

      <!-- STEP 3: Style -->
      <div class="onboard-step" id="step-3">
        <h1 class="header-title" style="font-size:1.8rem;margin-bottom:10px;">Formatting Tone</h1>
        <p class="header-sub" style="margin-bottom:16px;">How should the AI naturally format your speech?</p>
        
        <input type="hidden" name="speaking_style" id="ob_style_input" value="Casual">
        <div class="style-picker">
          <div class="style-card selected" onclick="selectStyle(this, 'Casual')">
            <div class="style-title">Casual</div>
            <div class="style-desc">Natural punctuation. Good for chats.</div>
          </div>
          <div class="style-card" onclick="selectStyle(this, 'Formal')">
            <div class="style-title">Formal</div>
            <div class="style-desc">Strict grammar. Perfect for emails.</div>
          </div>
          <div class="style-card" onclick="selectStyle(this, 'Code')">
            <div class="style-title">Code</div>
            <div class="style-desc">Formats symbols, camelCase natively.</div>
          </div>
          <div class="style-card" onclick="selectStyle(this, 'Serious')">
            <div class="style-title">Serious</div>
            <div class="style-desc">Concise, direct, no filler words.</div>
          </div>
        </div>

        <div style="display:flex;gap:12px;margin-top:20px;">
          <button type="button" class="btn btn-outline" style="flex:1;padding:14px;border-radius:24px;" onclick="nextStep(2)">Back</button>
          <button type="submit" class="btn btn-primary" style="flex:1;padding:14px;border-radius:24px;">Complete Setup</button>
        </div>
      </div>

    </form>
  </div>
</div>

<script>
function nextStep(step) {
  document.querySelectorAll('.onboard-step').forEach(el => el.classList.remove('active'));
  document.getElementById('step-' + step).classList.add('active');
}

function selectStyle(el, val) {
  document.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  document.getElementById('ob_style_input').value = val;
}
</script>

{% else %}

<!-- SIDEBAR LAYOUT -->
<div class="app-container">
  <aside class="sidebar">
    <div class="brand">
      <div class="brand-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:20px;height:20px;"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v1a7 7 0 0 1-14 0v-1M12 19v3M8 22h8"/></svg>
      </div>
      <div class="brand-text">JustSay</div>
    </div>

    <div class="nav-item active" onclick="showSection('overview',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
      Overview
    </div>
    <div class="nav-item" onclick="showSection('history',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      Transcripts
    </div>
    <div class="nav-item" onclick="showSection('dictionary',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
      Vocabulary
    </div>
    <div class="nav-item" onclick="showSection('prompts',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
      AI Rules
    </div>
    <div class="nav-item" onclick="showSection('settings',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
      Preferences
    </div>

    <div class="sidebar-bottom">
      <div class="nav-item" onclick="toggleTheme()">
        <span id="theme-icon" style="font-size:1.1rem">{{ "🌙" if theme == "dark" else "☀️" }}</span>
        <span id="theme-label" style="margin-left: 8px">{{ "Dark Theme" if theme == "dark" else "Light Theme" }}</span>
      </div>
      <div class="version-tag">v13</div>
    </div>
  </aside>

  <!-- MAIN -->
  <main class="main-content">

    <!-- OVERVIEW -->
    <div id="sec-overview" class="section active">
      <h1 class="header-title">Overview</h1>
      <p class="header-sub">Operational summary of local speech sessions.</p>
      
      <div class="card-grid">
        <div class="card">
          <div class="card-title">Dictations</div>
          <div class="card-value">{{ stats.total_dictations }}</div>
          <div class="card-desc">Recorded voice inputs</div>
        </div>
        <div class="card">
          <div class="card-title">Words Logged</div>
          <div class="card-value">{{ stats.total_words }}</div>
          <div class="card-desc">Words typed via microphone</div>
        </div>
        <div class="card">
          <div class="card-title">Speech Flow</div>
          <div class="card-value" style="font-size:1.8rem;padding-top:12px;">{{ insight_label }}</div>
          <div class="card-desc">Score: {{ insight_score }}/100</div>
        </div>
      </div>

      <div class="card">
        <div class="card-title" style="margin-bottom:20px">Active Shortcuts</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
          <div class="shortcut-box">
            <div class="shortcut-keys">{% for k in settings.hotkey_ptt.split('+') %}<kbd>{{ k.upper() }}</kbd>{% endfor %}</div>
            <div style="font-weight:600;margin:10px 0 4px;font-size:1rem">Push-to-Talk (Hold)</div>
            <div class="card-desc">Hold to record, release to transcribe.</div>
          </div>
          <div class="shortcut-box">
            <div class="shortcut-keys">{% for k in settings.hotkey_toggle.split('+') %}<kbd>{{ k.upper() }}</kbd>{% endfor %}</div>
            <div style="font-weight:600;margin:10px 0 4px;font-size:1rem">Toggle Recording (Tap)</div>
            <div class="card-desc">Tap once to begin, tap again to paste.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- HISTORY -->
    <div id="sec-history" class="section">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <h1 class="header-title">Transcripts</h1>
          <p class="header-sub">On-device transcripts history. Audio is discarded automatically.</p>
        </div>
        <form action="/clear_history" method="POST" onsubmit="return confirm('Wipe all local recordings permanently?')">
          <button type="submit" class="btn btn-danger" style="border-radius:24px">Clear Logs</button>
        </form>
      </div>
      
      <div class="card" style="padding:0; border:none; background:transparent">
        <div class="table-wrap">
          <table style="background:var(--surface); border-radius:var(--r-xl); overflow:hidden;">
            <thead><tr><th>Timestamp</th><th>Transcript</th><th>Words</th></tr></thead>
            <tbody>
            {% for h in history %}
            <tr>
              <td style="color:var(--text-muted);white-space:nowrap">{{ h.timestamp }}</td>
              <td style="max-width:500px;line-height:1.6">{{ h.transcript }}</td>
              <td><span class="tag" style="display:inline-flex;padding:4px 10px;font-size:0.75rem">{{ h.word_count }}</span></td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="text-align:center;padding:80px;color:var(--text-muted);">No local recordings found.</td></tr>
            {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- VOCABULARY -->
    <div id="sec-dictionary" class="section">
      <h1 class="header-title">Vocabulary</h1>
      <p class="header-sub">Define custom names, project terms, or jargon to improve accuracy.</p>
      
      <div class="card">
        <form action="/add_to_dictionary" method="POST" class="form-row" style="margin-bottom: 24px;">
          <input type="text" name="word" placeholder="e.g. Kubernetes, Antigravity" required style="max-width:400px;border-radius:24px">
          <button type="submit" class="btn btn-primary" style="border-radius:24px">Add Word</button>
        </form>

        <div class="card-title">Active Terms</div>
        <div class="tags">
          {% for word in dictionary %}
            <div class="tag">
              <span>{{ word }}</span>
              <a href="/delete_from_dictionary/{{ word }}">&times;</a>
            </div>
          {% else %}
            <span style="color:var(--text-muted);font-size:0.9rem">No vocabulary terms added yet.</span>
          {% endfor %}
        </div>
      </div>
    </div>

    <!-- PROMPTS -->
    <div id="sec-prompts" class="section">
      <h1 class="header-title">AI Rules</h1>
      <p class="header-sub">Supply custom instructions to format or structure the output text.</p>
      
      <div class="card" style="margin-bottom:24px">
        <form action="/add_prompt" method="POST" class="form-row">
          <input type="text" name="prompt_text" placeholder="e.g. Capitalize acronyms. Use bullet points." required style="flex:1;border-radius:24px">
          <button type="submit" class="btn btn-primary" style="border-radius:24px">Add Rule</button>
        </form>
      </div>

      <div class="card" style="padding:0; border:none; background:transparent">
        <div class="table-wrap">
          <table style="background:var(--surface); border-radius:var(--r-xl); overflow:hidden;">
            <thead><tr><th>Status</th><th>Rule Details</th><th style="text-align:right">Action</th></tr></thead>
            <tbody>
            {% for p in prompts %}
            <tr>
              <td style="width:140px">
                {% if p.is_active %}<span style="color:var(--accent);font-weight:600">Active</span>
                {% else %}<a href="/set_active/{{ p.id }}" style="color:var(--text);font-weight:500">Activate</a>{% endif %}
              </td>
              <td style="font-weight:400">{{ p.prompt_text }}</td>
              <td style="text-align:right"><a href="/delete_prompt/{{ p.id }}" style="color:var(--danger);font-weight:500;text-decoration:none">Remove</a></td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="text-align:center;padding:60px;color:var(--text-muted);">No rules added.</td></tr>
            {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- SETTINGS -->
    <div id="sec-settings" class="section">
      <h1 class="header-title">Preferences</h1>
      <p class="header-sub">Configure system shortcuts and formatting tones.</p>
      
      <div class="card">
        <form action="/update_settings" method="POST">
          <div class="form-group">
            <label class="form-label">Active Formatting Tone</label>
            <select name="speaking_style" style="max-width:400px;border-radius:12px">
              <option value="Casual" {{ 'selected' if settings.speaking_style == 'Casual' }}>Casual (conversational and natural)</option>
              <option value="Formal" {{ 'selected' if settings.speaking_style == 'Formal' }}>Formal (strictly formatted)</option>
              <option value="Serious" {{ 'selected' if settings.speaking_style == 'Serious' }}>Serious (concise and direct)</option>
              <option value="Code" {{ 'selected' if settings.speaking_style == 'Code' }}>Code (inserts syntax characters)</option>
            </select>
          </div>
          
          <div class="form-group" style="max-width:400px">
            <label class="form-label">Push-to-Talk Hotkey</label>
            <div style="display:flex;gap:12px;align-items:center;">
              <input type="hidden" name="hotkey_ptt" id="settings_ptt_input" value="{{ settings.hotkey_ptt }}">
              <div id="settings_ptt_input_display" class="shortcut-keys" style="flex:1;">
                {% for k in settings.hotkey_ptt.split('+') %}<kbd>{{ k.upper() }}</kbd>{% endfor %}
              </div>
              <button type="button" class="btn btn-outline" style="border-radius:24px" onclick="startRecording(this, 'settings_ptt_input')">Record</button>
            </div>
          </div>
          
          <div class="form-group" style="max-width:400px">
            <label class="form-label">Toggle Recording Hotkey</label>
            <div style="display:flex;gap:12px;align-items:center;">
              <input type="hidden" name="hotkey_toggle" id="settings_toggle_input" value="{{ settings.hotkey_toggle }}">
              <div id="settings_toggle_input_display" class="shortcut-keys" style="flex:1;">
                {% for k in settings.hotkey_toggle.split('+') %}<kbd>{{ k.upper() }}</kbd>{% endfor %}
              </div>
              <button type="button" class="btn btn-outline" style="border-radius:24px" onclick="startRecording(this, 'settings_toggle_input')">Record</button>
            </div>
          </div>
          
          <div class="form-group" style="display:flex;align-items:center;gap:12px;margin-top:30px">
            <input type="checkbox" name="show_ui" value="1" id="showUI" {{ 'checked' if settings.get('show_ui', True) else '' }} style="width:18px;height:18px;accent-color:var(--accent)">
            <label for="showUI" class="form-label" style="margin:0;cursor:pointer">Show Overlay Widget</label>
          </div>
          
          <input type="hidden" name="theme" id="theme-input" value="{{ theme }}">
          <button type="submit" class="btn btn-primary" style="margin-top:20px;width:200px;border-radius:24px">Save Preferences</button>
        </form>
      </div>
    </div>

  </main>
</div>

<script>
function showSection(name, el) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('sec-' + name).classList.add('active');
  if (el) el.classList.add('active');
}

function toggleTheme() {
  const html = document.documentElement;
  const cur = html.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  document.getElementById('theme-icon').textContent = next === 'dark' ? '🌙' : '☀️';
  document.getElementById('theme-label').textContent = next === 'dark' ? 'Dark Theme' : 'Light Theme';
  if (document.getElementById('theme-input')) document.getElementById('theme-input').value = next;
  
  fetch('/api/set_theme', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({theme: next})
  });
}
</script>
{% endif %}

<!-- INTERACTIVE HOTKEY RECORDER SCRIPT -->
<script>
let recordingInputInfo = null;

function startRecording(btn, inputId) {
    if (recordingInputInfo) {
        stopRecording();
    }
    recordingInputInfo = { btn, inputId };
    btn.textContent = "Listening...";
    btn.classList.add("recording-active");
    window.addEventListener('keydown', handleKeydown, {capture: true});
}

function handleKeydown(e) {
    e.preventDefault();
    e.stopPropagation();
    
    let keys = [];
    if (e.ctrlKey) keys.push('ctrl');
    if (e.metaKey) keys.push('windows');
    if (e.altKey) keys.push('alt');
    if (e.shiftKey) keys.push('shift');
    
    let key = e.key.toLowerCase();
    let isModifier = ['control', 'meta', 'alt', 'shift', 'os'].includes(key);
    
    if (!isModifier) {
        if (key === ' ') key = 'space';
        keys.push(key);
    }
    
    if (keys.length > 0) {
        const combo = keys.join('+');
        document.getElementById(recordingInputInfo.inputId).value = combo;
        document.getElementById(recordingInputInfo.inputId + '_display').innerHTML = combo.split('+').map(k => `<kbd>${k.toUpperCase()}</kbd>`).join('');
    }
    
    if (!isModifier) {
        stopRecording();
    }
}

function stopRecording() {
    if (!recordingInputInfo) return;
    window.removeEventListener('keydown', handleKeydown, {capture: true});
    recordingInputInfo.btn.textContent = "Record";
    recordingInputInfo.btn.classList.remove("recording-active");
    recordingInputInfo = null;
}
</script>

</body>
</html>"""


@app.route("/")
def index():
    settings = database.get_user_settings("localuser@localhost")
    if not settings:
        settings = {'speaking_style': 'Casual', 'theme': 'dark', 'hotkey_ptt': 'ctrl+windows',
                    'hotkey_toggle': 'ctrl+windows+space', 'onboarded': False, 'show_ui': True}

    theme = (settings.get('theme') or 'dark').lower()

    history_raw = database.get_history()
    history = []
    for h in history_raw:
        h['audio_filename'] = get_audio_filename(h.get('audio_path', ''))
        history.append(h)

    prompts = database.get_all_prompts()
    stats = database.get_statistics()
    dictionary = database.get_dictionary()
    insight_label, insight_score = generate_insights(history_raw)

    return render_template_string(HTML,
                                  settings=settings, theme=theme,
                                  history=history, prompts=prompts, stats=stats,
                                  dictionary=dictionary, insight_label=insight_label, insight_score=insight_score)


@app.route("/complete_onboarding", methods=["POST"])
def complete_onboarding():
    style = request.form.get("speaking_style", "Casual")
    ptt = request.form.get("hotkey_ptt", "ctrl+windows")
    toggle = request.form.get("hotkey_toggle", "ctrl+windows+space")
    database.update_user_settings(
        "localuser@localhost", style, "dark", ptt, toggle, onboarded=1, show_ui=1)
    return redirect(url_for("index"))


@app.route("/update_settings", methods=["POST"])
def update_settings():
    style = request.form.get("speaking_style", "Casual")
    theme = request.form.get("theme", "dark")
    ptt = request.form.get("hotkey_ptt", "ctrl+windows")
    toggle = request.form.get("hotkey_toggle", "ctrl+windows+space")
    show_ui = 1 if request.form.get("show_ui") == "1" else 0
    database.update_user_settings(
        "localuser@localhost", style, theme, ptt, toggle, onboarded=1, show_ui=show_ui)
    return redirect(url_for("index"))


@app.route("/api/set_theme", methods=["POST"])
def set_theme_api():
    data = request.get_json() or {}
    s = database.get_user_settings("localuser@localhost")
    if s:
        database.update_user_settings("localuser@localhost", s['speaking_style'], data.get(
            'theme', 'dark'), s['hotkey_ptt'], s['hotkey_toggle'], s['onboarded'], s.get('show_ui', 1))
    return jsonify({"ok": True})


@app.route("/add_to_dictionary", methods=["POST"])
def add_to_dict():
    word = request.form.get("word")
    if word and word.strip():
        database.add_to_dictionary(word.strip())
    return redirect(url_for("index"))


@app.route("/delete_from_dictionary/<word>")
def delete_from_dict(word):
    conn = sqlite3.connect(database.DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM dictionary WHERE word=?", (word,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/clear_history", methods=["POST"])
def clear_history():
    database.clear_history()
    audio_dir = database.AUDIO_DIR
    if os.path.exists(audio_dir):
        for f in os.listdir(audio_dir):
            try:
                os.remove(os.path.join(audio_dir, f))
            except:
                pass
    return redirect(url_for("index"))


@app.route("/add_prompt", methods=["POST"])
def add_prompt():
    t = request.form.get("prompt_text")
    if t:
        database.add_prompt(t)
    return redirect(url_for("index"))


@app.route("/set_active/<int:pid>")
def set_active(pid):
    database.set_active_prompt(pid)
    return redirect(url_for("index"))


@app.route("/delete_prompt/<int:pid>")
def delete_prompt(pid):
    database.delete_prompt(pid)
    return redirect(url_for("index"))


@app.route("/audio/<filename>")
def get_audio(filename):
    audio_dir = database.AUDIO_DIR
    return send_file(os.path.join(audio_dir, filename))


def run_server():
    database.init_db()
    # Suppress flask output
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host="127.0.0.1", port=2000, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_server()
