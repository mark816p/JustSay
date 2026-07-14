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
    score = int(min(100, max(0, 100 - (filler_count / max(len(words), 1)) * 400)))
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
<title>JustSay — Local Voice Dictation</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root {
  --r-lg: 12px;
  --r-md: 8px;
  --r-sm: 4px;
  --accent: #4b5563;
  --accent-light: #9ca3af;
  --danger: #ef4444;
  --success: #10b981;
  --trans: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
  --font-mono: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
}

[data-theme=dark]{
  --bg: #121214;
  --bg-sidebar: #18181c;
  --bg-card: #1c1c22;
  --bg-hover: #26262f;
  --border: #2d2d37;
  --border-focus: #4b5563;
  --text: #f3f4f6;
  --text-muted: #9ca3af;
  --shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

[data-theme=light]{
  --bg: #f3f4f6;
  --bg-sidebar: #ffffff;
  --bg-card: #ffffff;
  --bg-hover: #f9fafb;
  --border: #e5e7eb;
  --border-focus: #9ca3af;
  --text: #1f2937;
  --text-muted: #6b7280;
  --shadow: 0 4px 12px rgba(0,0,0,0.05);
}

body {
  font-family: var(--font-sans);
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  transition: background 0.2s, color 0.2s;
  -webkit-font-smoothing: antialiased;
}

/* ONBOARDING LAYOUT */
.onboard-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  background: var(--bg);
}

.onboard-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 40px;
  max-width: 500px;
  width: 100%;
  box-shadow: var(--shadow);
  text-align: center;
}

.onboard-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--bg-hover);
  border: 1.5px solid var(--border);
  margin-bottom: 24px;
  color: var(--text);
}

.onboard-title {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.onboard-desc {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin-bottom: 30px;
  line-height: 1.5;
}

/* SIDEBAR LAYOUT */
.layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 250px;
  min-width: 250px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 30px 0;
  position: sticky;
  top: 0;
  height: 100vh;
  z-index: 10;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 24px 20px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
}

.sidebar-logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  color: var(--text);
}

.logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: var(--text);
}

.logo-sub {
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-top: 1px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.nav-section-title {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 16px 24px 6px;
  opacity: 0.8;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 24px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: var(--trans);
  text-decoration: none;
}

.nav-item:hover, .nav-item.active {
  color: var(--text);
  background: var(--bg-hover);
  border-left-color: var(--text);
}

.nav-item svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  opacity: 0.7;
}

.nav-item:hover svg, .nav-item.active svg {
  opacity: 1;
}

.sidebar-bottom {
  margin-top: auto;
  padding: 20px 24px 0;
  border-top: 1px solid var(--border);
}

.theme-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 10px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text);
  width: 100%;
  transition: var(--trans);
}

.theme-btn:hover {
  border-color: var(--border-focus);
}

/* MAIN */
.main {
  flex: 1;
  padding: 40px 50px;
  overflow-y: auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin-bottom: 6px;
}

.page-header p {
  color: var(--text-muted);
  font-size: 0.85rem;
  font-weight: 500;
}

/* GRID & CARDS */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 24px;
  transition: var(--trans);
}

.stat-card:hover {
  border-color: var(--border-focus);
  box-shadow: var(--shadow);
}

.stat-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 2.2rem;
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 4px;
}

.stat-sub {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 28px;
  margin-bottom: 20px;
}

.card-title {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 6px;
}

.card-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 20px;
}

/* INPUTS */
.form-group {
  margin-bottom: 16px;
  text-align: left;
}

.form-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
}

input[type=text], select {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 10px 14px;
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 0.85rem;
  font-weight: 500;
  width: 100%;
  transition: var(--trans);
  outline: none;
}

input[type=text]:focus, select:focus {
  border-color: var(--border-focus);
}

/* BUTTONS */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--r-md);
  padding: 10px 18px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: var(--trans);
  text-decoration: none;
  white-space: nowrap;
}

.btn:hover {
  background: var(--accent-light);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 0.75rem;
  border-radius: var(--r-sm);
}

.btn-ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}

.btn-ghost:hover {
  background: var(--bg-hover);
}

.btn-danger {
  background: var(--danger);
}
.btn-danger:hover {
  background: #f87171;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}

.btn-outline:hover {
  background: var(--bg-hover);
}

.form-row {
  display: flex;
  gap: 10px;
}
.form-row input {
  flex: 1;
}

/* TABLES */
.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  text-align: left;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

td {
  padding: 12px 16px;
  font-size: 0.85rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

tr:last-child td {
  border-bottom: none;
}

tr:hover td {
  background: var(--bg-hover);
}

/* TAGS */
.tag-container {
  display: flex;
  align-items: center;
  background: var(--bg);
  border: 1px solid var(--border);
  padding: 4px 10px;
  border-radius: var(--r-lg);
  font-size: 0.8rem;
  font-weight: 600;
  gap: 8px;
}

.tag-delete {
  color: var(--danger);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
}

.badge-active {
  background: rgba(16, 185, 129, 0.12);
  color: var(--success);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.badge-neutral {
  background: var(--bg);
  color: var(--text-muted);
  border: 1px solid var(--border);
}

/* SHORTCUTS */
.shortcut-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.shortcut-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 18px;
}

.shortcut-keys {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
}

kbd {
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-bottom: 2.5px solid var(--border);
  border-radius: 4px;
  padding: 2px 8px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text);
}

.shortcut-desc {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.4;
}

/* AUDIO */
.audio-container {
  display: flex;
  align-items: center;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 4px;
  max-width: 280px;
}

audio {
  height: 30px;
  width: 100%;
}

/* BANNER */
.privacy-banner {
  background: rgba(75, 85, 99, 0.08);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 12px 16px;
  margin-bottom: 20px;
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.4;
}

/* PROGRESS */
.progress-bar {
  background: var(--bg);
  border-radius: 99px;
  height: 6px;
  margin-top: 10px;
  overflow: hidden;
  border: 1px solid var(--border);
}

.progress-fill {
  height: 100%;
  background: var(--accent-light);
}

/* TABS */
.section {
  display: none;
}
.section.active {
  display: block;
}
</style>
</head>
<body>

{% if not settings.onboarded %}
<!-- ONBOARDING FLOW -->
<div class="onboard-container">
  <div class="onboard-card">
    <div class="onboard-logo">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:28px;height:28px;"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v1a7 7 0 0 1-14 0v-1M12 19v3M8 22h8"/></svg>
    </div>
    <div class="onboard-title">Welcome to JustSay</div>
    <div class="onboard-desc">Set up your local speech dictation preferences to get started. All voice recognition processes run 100% offline.</div>
    
    <form action="/complete_onboarding" method="POST">
      <div class="form-group">
        <label class="form-label">Formatting Style & Tone</label>
        <select name="speaking_style">
          <option value="Casual">Casual (conversational and natural)</option>
          <option value="Formal">Formal (strictly formatted, professional)</option>
          <option value="Serious">Serious (concise and direct)</option>
          <option value="Code">Code (inserts syntax characters)</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Push-to-Talk Shortcut</label>
        <input type="text" name="hotkey_ptt" value="ctrl+windows" required>
      </div>

      <div class="form-group">
        <label class="form-label">Toggle Recording Shortcut</label>
        <input type="text" name="hotkey_toggle" value="ctrl+windows+space" required>
      </div>

      <button type="submit" class="btn" style="width:100%;margin-top:10px;">Get Started</button>
    </form>
  </div>
</div>
{% else %}

<!-- SIDEBAR LAYOUT -->
<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="sidebar-logo-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="width:16px;height:16px;"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v1a7 7 0 0 1-14 0v-1M12 19v3M8 22h8"/></svg>
      </div>
      <div>
        <div class="logo-text">JustSay</div>
        <div class="logo-sub">Local Voice OS</div>
      </div>
    </div>

    <span class="nav-section-title">Telemetry</span>
    <a class="nav-item active" onclick="showSection('overview',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
      Overview
    </a>
    <a class="nav-item" onclick="showSection('history',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      History Logs
    </a>
    
    <span class="nav-section-title">Settings</span>
    <a class="nav-item" onclick="showSection('dictionary',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
      Vocabulary
    </a>
    <a class="nav-item" onclick="showSection('prompts',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
      AI Rules
    </a>
    <a class="nav-item" onclick="showSection('shortcuts',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="2" y="4" width="20" height="16" rx="2" ry="2"/><path d="M6 8h.01M10 8h.01M14 8h.01M18 8h.01M6 12h.01M10 12h.01M14 12h.01M18 12h.01M7 16h10"/></svg>
      Shortcuts
    </a>
    <a class="nav-item" onclick="showSection('preferences',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
      Preferences
    </a>

    <div class="sidebar-bottom">
      <button class="theme-btn" onclick="toggleTheme()">
        <span id="theme-icon">{{ "🌙" if theme == "dark" else "☀️" }}</span>
        <span id="theme-label">{{ "Dark UI" if theme == "dark" else "Light UI" }}</span>
      </button>
    </div>
  </aside>

  <!-- MAIN -->
  <main class="main">

    <!-- OVERVIEW -->
    <div id="sec-overview" class="section active">
      <div class="page-header">
        <h1>Overview</h1>
        <p>Operational summary of local speech sessions.</p>
      </div>
      
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total Dictations</div>
          <div class="stat-value">{{ stats.total_dictations }}</div>
          <div class="stat-sub">Recorded voice inputs</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Words Logged</div>
          <div class="stat-value">{{ stats.total_words }}</div>
          <div class="stat-sub">Words typed via microphone</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Speech Flow</div>
          <div class="stat-value" style="font-size:1.2rem;padding-top:8px;font-weight:700">{{ insight_label }}</div>
          <div class="stat-sub">Pacing score</div>
          <div class="progress-bar"><div class="progress-fill" style="width:{{ insight_score }}%"></div></div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Shortcuts Configured</div>
        <div class="card-desc">Active system hotkeys. Customize these in the Preferences menu.</div>
        <div class="shortcut-grid">
          <div class="shortcut-card">
            <div class="shortcut-keys">
              {% for k in settings.hotkey_ptt.split('+') %}
                <kbd>{{ k.upper() }}</kbd>
              {% endfor %}
            </div>
            <div class="card-title" style="font-size:0.9rem;margin-bottom:4px">Push-to-Talk</div>
            <div class="shortcut-desc">Hold to record audio, release to transcribe.</div>
          </div>
          <div class="shortcut-card">
            <div class="shortcut-keys">
              {% for k in settings.hotkey_toggle.split('+') %}
                <kbd>{{ k.upper() }}</kbd>
              {% endfor %}
            </div>
            <div class="card-title" style="font-size:0.9rem;margin-bottom:4px">Toggle Recording</div>
            <div class="shortcut-desc">Press to start, press again to stop recording.</div>
          </div>
        </div>
      </div>

      <div class="privacy-banner">
        🔒 <strong>Local Sovereignty:</strong> &nbsp;This system runs offline. Transcription, audio archiving, settings, and custom dictionaries are saved strictly on this PC.
      </div>
    </div>

    <!-- HISTORY -->
    <div id="sec-history" class="section">
      <div class="page-header">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
          <div>
            <h1>History Logs</h1>
            <p>On-device transcripts and audio logs.</p>
          </div>
          <form action="/clear_history" method="POST" onsubmit="return confirm('Wipe all local recordings permanently?')">
            <button type="submit" class="btn btn-danger btn-sm">Clear Logs</button>
          </form>
        </div>
      </div>
      
      <div class="card" style="padding:0;overflow:hidden">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Timestamp</th><th>Transcript</th><th>Words</th><th>Audio Wave</th></tr></thead>
            <tbody>
            {% for h in history %}
            <tr>
              <td style="white-space:nowrap;color:var(--text-muted);font-size:0.8rem;font-family:var(--font-mono)">{{ h.timestamp }}</td>
              <td style="line-height:1.4;max-width:360px;font-weight:500">{{ h.transcript }}</td>
              <td><span class="badge badge-neutral">{{ h.word_count }}</span></td>
              <td>
                <div class="audio-container">
                  <audio controls><source src="/audio/{{ h.audio_filename }}" type="audio/wav"></audio>
                </div>
              </td>
            </tr>
            {% else %}
            <tr><td colspan="4" style="text-align:center;padding:48px;color:var(--text-muted);font-style:italic">No local recordings found.</td></tr>
            {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- VOCABULARY -->
    <div id="sec-dictionary" class="section">
      <div class="page-header">
        <h1>Local Vocabulary</h1>
        <p>Define custom names, project terms, or jargon. The neural transcriber uses these to improve matching accuracy.</p>
      </div>

      <div class="card">
        <div class="card-title">Add Custom Word</div>
        <form action="/add_to_dictionary" method="POST" class="form-row" style="margin-bottom: 24px;">
          <input type="text" name="word" placeholder="e.g. Kubernetes, Antigravity, Kinjal" required>
          <button type="submit" class="btn">Add Word</button>
        </form>

        <div class="card-title" style="margin-top: 20px;">Active Custom Terms</div>
        <div class="card-desc">Click the "x" next to a word to remove it from the database.</div>
        <div class="tags" style="display:flex;flex-wrap:wrap;gap:8px;">
          {% for word in dictionary %}
            <div class="tag-container">
              <span>{{ word }}</span>
              <a href="/delete_from_dictionary/{{ word }}" class="tag-delete">&times;</a>
            </div>
          {% else %}
            <span style="color:var(--text-muted);font-size:0.85rem;font-style:italic">No vocabulary terms added yet.</span>
          {% endfor %}
        </div>
      </div>
    </div>

    <!-- AI RULES / PROMPTS -->
    <div id="sec-prompts" class="section">
      <div class="page-header">
        <h1>AI Instruction Rules</h1>
        <p>Supply custom rules to format, capitalize, or structure the output text.</p>
      </div>
      
      <div class="card">
        <div class="card-title" style="margin-bottom:12px">Create Rule</div>
        <form action="/add_prompt" method="POST" class="form-row">
          <input type="text" name="prompt_text" placeholder="e.g. Capitalize acronyms. Use bullet points for lists." required>
          <button type="submit" class="btn">Add Rule</button>
        </form>
      </div>

      <div class="card" style="padding:0;overflow:hidden">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Rule Details</th><th style="text-align:right">Action</th></tr></thead>
            <tbody>
            {% for p in prompts %}
            <tr>
              <td style="width:140px">
                {% if p.is_active %}<span class="badge badge-active">Active</span>
                {% else %}<a href="/set_active/{{ p.id }}" class="btn btn-sm btn-outline">Activate</a>{% endif %}
              </td>
              <td style="font-weight:600">{{ p.prompt_text }}</td>
              <td style="text-align:right"><a href="/delete_prompt/{{ p.id }}" class="btn btn-sm btn-ghost" style="color:var(--danger);border-color:var(--danger)">Remove</a></td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="text-align:center;padding:48px;color:var(--text-muted);font-style:italic">No rules added.</td></tr>
            {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- SHORTCUTS VIEW -->
    <div id="sec-shortcuts" class="section">
      <div class="page-header">
        <h1>Keyboard Triggers</h1>
        <p>Global OS triggers. Tap or hold keys to dictation-type instantly.</p>
      </div>
      <div class="shortcut-grid" style="grid-template-columns:1fr;gap:16px">
        <div class="shortcut-card">
          <div class="shortcut-keys">
            {% for k in settings.hotkey_ptt.split('+') %}
              <kbd>{{ k.upper() }}</kbd>
            {% endfor %}
          </div>
          <div class="card-title" style="margin-bottom:8px">Push-to-Talk (Hold)</div>
          <div class="shortcut-desc">Hold down keys to capture audio. Release to transcribe and paste.</div>
        </div>
        <div class="shortcut-card">
          <div class="shortcut-keys">
            {% for k in settings.hotkey_toggle.split('+') %}
              <kbd>{{ k.upper() }}</kbd>
            {% endfor %}
          </div>
          <div class="card-title" style="margin-bottom:8px">Toggle Recording State (Tap)</div>
          <div class="shortcut-desc">Tap once to begin recording. Tap again to terminate recording and paste.</div>
        </div>
        <div class="shortcut-card">
          <div class="shortcut-keys"><kbd>Visual Overlay Pill</kbd></div>
          <div class="card-title" style="margin-bottom:8px">Learn Dictionary Terms</div>
          <div class="shortcut-desc">When dictation completes, a small button appears for 2 seconds on your taskbar pill. Tap it to quickly teach the system spelling corrections.</div>
        </div>
      </div>
    </div>

    <!-- PREFERENCES -->
    <div id="sec-preferences" class="section">
      <div class="page-header">
        <h1>Preferences</h1>
        <p>Manage application shortcut settings and default configurations.</p>
      </div>
      
      <div class="card">
        <div class="card-title">Dictation Preferences & Custom Keys</div>
        <div class="card-desc">Configure keys and speaking tones. Dynamic reloading handles updates instantly.</div>
        <form action="/update_settings" method="POST">
          <div class="form-group">
            <label class="form-label">Active Formatting Tone</label>
            <select name="speaking_style">
              <option value="Casual" {{ 'selected' if settings.speaking_style == 'Casual' }}>Casual (conversational and natural)</option>
              <option value="Formal" {{ 'selected' if settings.speaking_style == 'Formal' }}>Formal (strictly formatted, professional)</option>
              <option value="Serious" {{ 'selected' if settings.speaking_style == 'Serious' }}>Serious (concise and direct)</option>
              <option value="Code" {{ 'selected' if settings.speaking_style == 'Code' }}>Code (inserts syntax characters)</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">Push-to-Talk Hotkey</label>
            <input type="text" name="hotkey_ptt" value="{{ settings.hotkey_ptt }}" placeholder="e.g. ctrl+windows" required>
            <p style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;">Combine keys using "+" (e.g. ctrl+windows, ctrl+shift+z).</p>
          </div>

          <div class="form-group">
            <label class="form-label">Toggle Recording Hotkey</label>
            <input type="text" name="hotkey_toggle" value="{{ settings.hotkey_toggle }}" placeholder="e.g. ctrl+windows+space" required>
            <p style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;">Combine keys using "+" (e.g. ctrl+windows+space, alt+space).</p>
          </div>

          <input type="hidden" name="theme" id="theme-input" value="{{ theme }}">
          <button type="submit" class="btn">Save Preferences</button>
        </form>
      </div>
      
      <div class="card" style="border-color:var(--border)">
        <div class="card-title" style="color:var(--danger)">Wipe Database</div>
        <div class="card-desc">Erase history, customized vocab, and prompts.</div>
        <form action="/clear_history" method="POST" onsubmit="return confirm('Wipe local database parameters?')">
          <button type="submit" class="btn btn-danger">Erase Local Database</button>
        </form>
      </div>
    </div>

  </main>
</div>
{% endif %}

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
  document.getElementById('theme-label').textContent = next === 'dark' ? 'Dark UI' : 'Light UI';
  if (document.getElementById('theme-input')) document.getElementById('theme-input').value = next;
  
  fetch('/api/set_theme', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({theme: next})
  });
}
</script>
</body>
</html>"""

@app.route("/")
def index():
    settings = database.get_user_settings("localuser@localhost")
    if not settings:
        settings = {'speaking_style': 'Casual', 'theme': 'dark', 'hotkey_ptt': 'ctrl+windows', 'hotkey_toggle': 'ctrl+windows+space', 'onboarded': False}
    
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
    database.update_user_settings("localuser@localhost", style, "dark", ptt, toggle, onboarded=1)
    return redirect(url_for("index"))

@app.route("/update_settings", methods=["POST"])
def update_settings():
    style = request.form.get("speaking_style", "Casual")
    theme = request.form.get("theme", "dark")
    ptt = request.form.get("hotkey_ptt", "ctrl+windows")
    toggle = request.form.get("hotkey_toggle", "ctrl+windows+space")
    database.update_user_settings("localuser@localhost", style, theme, ptt, toggle, onboarded=1)
    return redirect(url_for("index"))

@app.route("/api/set_theme", methods=["POST"])
def set_theme_api():
    data = request.get_json() or {}
    s = database.get_user_settings("localuser@localhost")
    if s:
        database.update_user_settings("localuser@localhost", s['speaking_style'], data.get('theme', 'dark'), s['hotkey_ptt'], s['hotkey_toggle'], s['onboarded'])
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
            try: os.remove(os.path.join(audio_dir, f))
            except: pass
    return redirect(url_for("index"))

@app.route("/add_prompt", methods=["POST"])
def add_prompt():
    t = request.form.get("prompt_text")
    if t: database.add_prompt(t)
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
    pass
    app.run(host="127.0.0.1", port=2000, debug=False, use_reloader=False)

if __name__ == "__main__":
    run_server()
