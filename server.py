from flask import Flask, render_template_string, request, redirect, url_for, send_file, session, jsonify
from authlib.integrations.flask_client import OAuth
import database
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "js-local-secret-2024")

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID", "mock-client-id"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", "mock-client-secret"),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'openid email profile'},
)

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
        return "Conversational (Filler-Heavy)", score
    elif avg_len > 25:
        return "Expressive & Detailed", score
    elif avg_len < 6:
        return "Concise & Direct", score
    else:
        return "Fluent & Professional", score

HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="{{ theme }}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>JustSay — Local Voice Dictation Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root {
  --r-lg: 20px;
  --r-md: 14px;
  --r-sm: 8px;
  --accent: #6366f1;
  --accent-light: #818cf8;
  --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  --danger: #f43f5e;
  --danger-light: #fda4af;
  --success: #10b981;
  --trans: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

[data-theme=dark]{
  --bg: #09090b;
  --bg-sidebar: #0f0f13;
  --bg-card: rgba(20, 20, 27, 0.7);
  --bg-hover: rgba(30, 30, 42, 0.8);
  --border: rgba(255, 255, 255, 0.08);
  --border-focus: rgba(99, 102, 241, 0.4);
  --text: #fafafa;
  --text-muted: #8b8e9f;
  --shadow: 0 12px 40px -10px rgba(0, 0, 0, 0.6);
  --glow: rgba(99, 102, 241, 0.12);
  --glass-bg: rgba(9, 9, 11, 0.75);
}

[data-theme=light]{
  --bg: #f8fafc;
  --bg-sidebar: #ffffff;
  --bg-card: rgba(255, 255, 255, 0.85);
  --bg-hover: rgba(241, 245, 249, 0.9);
  --border: rgba(0, 0, 0, 0.06);
  --border-focus: rgba(99, 102, 241, 0.3);
  --text: #0f172a;
  --text-muted: #64748b;
  --shadow: 0 10px 30px -10px rgba(99, 102, 241, 0.05);
  --glow: rgba(99, 102, 241, 0.04);
  --glass-bg: rgba(255, 255, 255, 0.8);
}

body {
  font-family: var(--font-sans);
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  transition: background 0.3s, color 0.3s;
  -webkit-font-smoothing: antialiased;
}

/* APP LAYOUT */
.layout {
  display: flex;
  min-height: 100vh;
}

/* SIDEBAR */
.sidebar {
  width: 260px;
  min-width: 260px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 32px 0;
  position: sticky;
  top: 0;
  height: 100vh;
  z-index: 10;
}

.sidebar-logo {
  padding: 0 28px 24px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
}

.logo-text {
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-sub {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-muted);
  margin-top: 4px;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.nav-section-title {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 20px 28px 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 28px;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  border-left: 4px solid transparent;
  transition: var(--trans);
  text-decoration: none;
}

.nav-item:hover, .nav-item.active {
  color: var(--text);
  background: var(--bg-hover);
  border-left-color: var(--accent);
}

.nav-item svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  opacity: 0.7;
  transition: var(--trans);
}

.nav-item:hover svg, .nav-item.active svg {
  opacity: 1;
  color: var(--accent);
}

.sidebar-bottom {
  margin-top: auto;
  padding: 24px 28px 0;
  border-top: 1px solid var(--border);
}

.theme-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 12px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text);
  width: 100%;
  transition: var(--trans);
}

.theme-btn:hover {
  border-color: var(--accent);
}

/* MAIN CONTENT */
.main {
  flex: 1;
  padding: 48px 64px;
  overflow-y: auto;
  max-width: 1100px;
}

.page-header {
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: -0.75px;
  margin-bottom: 8px;
}

.page-header p {
  color: var(--text-muted);
  font-size: 0.95rem;
  font-weight: 500;
}

/* CARDS */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 28px;
  position: relative;
  overflow: hidden;
  transition: var(--trans);
}

.stat-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top right, var(--glow), transparent 70%);
  pointer-events: none;
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--accent);
  box-shadow: var(--shadow);
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.75px;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.stat-value {
  font-size: 2.8rem;
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 6px;
  letter-spacing: -1px;
}

.stat-value.accent {
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-sub {
  font-size: 0.85rem;
  color: var(--text-muted);
  font-weight: 500;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 32px;
  margin-bottom: 24px;
  transition: var(--trans);
}

.card:hover {
  border-color: var(--border-focus);
}

.card-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 6px;
  letter-spacing: -0.25px;
}

.card-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 24px;
  font-weight: 500;
}

/* FORMS & INPUTS */
.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

input[type=text], select, textarea {
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: var(--r-md);
  padding: 12px 16px;
  color: var(--text);
  font-family: var(--font-sans);
  font-size: 0.9rem;
  font-weight: 500;
  width: 100%;
  transition: var(--trans);
  outline: none;
}

input[type=text]:focus, select:focus, textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15);
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
  padding: 12px 24px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: var(--trans);
  text-decoration: none;
  white-space: nowrap;
}

.btn:hover {
  background: var(--accent-light);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
}

.btn:active {
  transform: translateY(0);
}

.btn-sm {
  padding: 8px 16px;
  font-size: 0.8rem;
  border-radius: var(--r-sm);
}

.btn-ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}

.btn-ghost:hover {
  background: var(--bg-hover);
  border-color: var(--text);
  color: var(--text);
  transform: none;
  box-shadow: none;
}

.btn-danger {
  background: var(--danger);
}
.btn-danger:hover {
  background: #f43f5e;
  box-shadow: 0 4px 12px rgba(244, 63, 94, 0.2);
}

.btn-outline-accent {
  background: transparent;
  border: 1.5px solid var(--accent);
  color: var(--accent);
}

.btn-outline-accent:hover {
  background: var(--accent);
  color: #fff;
}

.form-row {
  display: flex;
  gap: 12px;
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
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 16px 20px;
  border-bottom: 1.5px solid var(--border);
}

td {
  padding: 16px 20px;
  font-size: 0.9rem;
  font-weight: 500;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

tr:last-child td {
  border-bottom: none;
}

tr:hover td {
  background: var(--bg-hover);
}

/* BADGES & CHIPS */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.25px;
}

.badge-active {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.badge-accent {
  background: rgba(99, 102, 241, 0.1);
  color: var(--accent);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  background: var(--bg);
  color: var(--accent);
  border: 1px solid var(--border);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  transition: var(--trans);
}

.tag:hover {
  border-color: var(--accent);
  background: var(--bg-hover);
}

/* SHORTCUT CARDS */
.shortcut-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.shortcut-card {
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: var(--r-md);
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.shortcut-keys {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

kbd {
  background: var(--bg-sidebar);
  border: 1px solid var(--border);
  border-bottom: 3.5px solid var(--border);
  border-radius: 6px;
  padding: 4px 10px;
  font-family: var(--font-mono);
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text);
  box-shadow: 0 2px 0 rgba(0,0,0,0.05);
}

.shortcut-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  font-weight: 500;
  line-height: 1.5;
}

/* CUSTOM AUDIO CONTROLS WRAPPER */
.audio-container {
  display: flex;
  align-items: center;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 6px 12px;
  max-width: 320px;
}

audio {
  height: 36px;
  width: 100%;
  border-radius: var(--r-sm);
  outline: none;
}

/* PRIVACY BANNER */
.privacy-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(16, 185, 129, 0.06);
  border: 1px solid rgba(16, 185, 129, 0.15);
  border-radius: var(--r-md);
  padding: 16px 20px;
  margin-bottom: 24px;
  font-size: 0.88rem;
  color: var(--text-muted);
  font-weight: 500;
  line-height: 1.5;
}

.privacy-banner strong {
  color: var(--success);
}

/* PROGRESS BAR */
.progress-bar {
  background: var(--bg);
  border-radius: 99px;
  height: 8px;
  margin-top: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
}

.progress-fill {
  height: 100%;
  border-radius: 99px;
  background: var(--accent-gradient);
  transition: width 0.5s ease;
}

/* USER PROFILE INFO */
.user-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 28px 24px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 12px;
}

.user-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--accent-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1rem;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
}

.user-details {
  overflow: hidden;
}

.user-name {
  font-size: 0.9rem;
  font-weight: 700;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-email {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* SECTION TRANSITIONS */
.section {
  display: none;
  animation: fadeIn 0.3s ease;
}
.section.active {
  display: block;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

/* SCROLLBAR */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
</head>
<body>

<div class="layout">
  <!-- SIDEBAR -->
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="logo-text">JustSay</div>
      <div class="logo-sub">Private Audio OS</div>
    </div>

    {% if user %}
    <div class="user-chip">
      <div class="user-avatar">{{ user.name[0].upper() }}</div>
      <div class="user-details">
        <div class="user-name">{{ user.name }}</div>
        <div class="user-email">{{ user.email }}</div>
      </div>
    </div>
    {% endif %}

    <span class="nav-section-title">Analysis & Logs</span>
    <a class="nav-item active" onclick="showSection('overview',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>
      Overview
    </a>
    <a class="nav-item" onclick="showSection('history',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      History logs
    </a>
    
    <span class="nav-section-title">Customisation</span>
    <a class="nav-item" onclick="showSection('dictionary',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
      Vocabulary
    </a>
    <a class="nav-item" onclick="showSection('prompts',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
      Instructions
    </a>

    <span class="nav-section-title">Configuration</span>
    <a class="nav-item" onclick="showSection('shortcuts',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="2" y="4" width="20" height="16" rx="2" ry="2"/><path d="M6 8h.01M10 8h.01M14 8h.01M18 8h.01M6 12h.01M10 12h.01M14 12h.01M18 12h.01M7 16h10"/></svg>
      Shortcuts
    </a>
    <a class="nav-item" onclick="showSection('settings',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
      Preferences
    </a>

    <div class="sidebar-bottom">
      {% if user %}
        <a href="/logout" class="btn btn-ghost" style="width:100%;margin-bottom:12px">Sign Out</a>
      {% else %}
        <a href="/login" class="btn" style="width:100%;margin-bottom:12px">Sign In (Google)</a>
      {% endif %}
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
        <p>Real-time analytics and telemetry of your local voice sessions.</p>
      </div>
      
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total Dictations</div>
          <div class="stat-value accent">{{ stats.total_dictations }}</div>
          <div class="stat-sub">Completed sessions</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Words Logged</div>
          <div class="stat-value accent">{{ stats.total_words }}</div>
          <div class="stat-sub">Words typed via audio</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Speaking Rhythm</div>
          <div class="stat-value" style="font-size:1.3rem;padding-top:10px;font-weight:700">{{ insight_label }}</div>
          <div class="stat-sub">Vocabulary flow index</div>
          <div class="progress-bar"><div class="progress-fill" style="width:{{ insight_score }}%"></div></div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Direct Shortcuts</div>
        <div class="card-desc">JustSay runs transparently in the background. Use these keys in any app.</div>
        <div class="shortcut-grid">
          <div class="shortcut-card">
            <div>
              <div class="shortcut-keys"><kbd>Ctrl</kbd><span>+</span><kbd>Win</kbd></div>
              <div class="card-title" style="font-size:0.95rem;margin-bottom:4px">Push-to-Talk</div>
              <div class="shortcut-desc">Hold keys to record audio. Release them to transcribe and paste instantly.</div>
            </div>
          </div>
          <div class="shortcut-card">
            <div>
              <div class="shortcut-keys"><kbd>Ctrl</kbd><span>+</span><kbd>Win</kbd><span>+</span><kbd>Space</kbd></div>
              <div class="card-title" style="font-size:0.95rem;margin-bottom:4px">Toggle Recording</div>
              <div class="shortcut-desc">Press once to start recording. Press again to finish. Useful for long speech.</div>
            </div>
          </div>
        </div>
      </div>

      <div class="privacy-banner">
        🔒 <strong>Local Isolation:</strong> &nbsp;This system does not dispatch data to cloud servers. All neural model evaluation is conducted locally on your computer.
      </div>
    </div>

    <!-- HISTORY -->
    <div id="sec-history" class="section">
      <div class="page-header">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
          <div>
            <h1>History Logs</h1>
            <p>Your previous transcriptions and audio captures.</p>
          </div>
          <form action="/clear_history" method="POST" onsubmit="return confirm('Wipe all local recordings and logs permanently?')">
            <button type="submit" class="btn btn-danger btn-sm">Clear Log History</button>
          </form>
        </div>
      </div>
      
      <div class="card" style="padding:0;overflow:hidden">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Timestamp</th><th>Transcribed Content</th><th>Length</th><th>Audio Wave</th></tr></thead>
            <tbody>
            {% for h in history %}
            <tr>
              <td style="white-space:nowrap;color:var(--text-muted);font-size:0.8rem;font-family:var(--font-mono)">{{ h.timestamp }}</td>
              <td style="line-height:1.5;max-width:380px;font-weight:500">{{ h.transcript }}</td>
              <td><span class="badge badge-accent">{{ h.word_count }} words</span></td>
              <td>
                <div class="audio-container">
                  <audio controls><source src="/audio/{{ h.audio_filename }}" type="audio/wav"></audio>
                </div>
              </td>
            </tr>
            {% else %}
            <tr><td colspan="4" style="text-align:center;padding:48px;color:var(--text-muted);font-style:italic">No local voice sessions logged yet.</td></tr>
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
        <p>Custom dictionary names, jargon, and words the transcription engine will prioritize.</p>
      </div>
      <div class="card">
        <div class="card-title">Known Vocabulary Terms</div>
        <div class="card-desc">Clicking "Undo & Correct" on the visual waveform pill appends terms here.</div>
        <div class="tags">
          {% for word in dictionary %}
            <span class="tag">{{ word }}</span>
          {% else %}
            <span style="color:var(--text-muted);font-size:0.9rem;font-style:italic">Your customized dictionary is currently empty. Use the quick Undo pill when dictating to add corrections.</span>
          {% endfor %}
        </div>
      </div>
    </div>

    <!-- INSTRUCTIONS -->
    <div id="sec-prompts" class="section">
      <div class="page-header">
        <h1>AI Formatting Instructions</h1>
        <p>Specify prompts to guide structural formatting (e.g. casing, styling, code formatting).</p>
      </div>
      
      <div class="card">
        <div class="card-title" style="margin-bottom:12px">Create Formatting Rule</div>
        <form action="/add_prompt" method="POST" class="form-row">
          <input type="text" name="prompt_text" placeholder="e.g. Always write code blocks in markdown. Format dates as DD-MM-YYYY." required>
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
                {% else %}<a href="/set_active/{{ p.id }}" class="btn btn-sm btn-outline-accent">Activate</a>{% endif %}
              </td>
              <td style="font-weight:600">{{ p.prompt_text }}</td>
              <td style="text-align:right"><a href="/delete_prompt/{{ p.id }}" class="btn btn-sm btn-ghost" style="color:var(--danger);border-color:var(--danger)">Remove</a></td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="text-align:center;padding:48px;color:var(--text-muted);font-style:italic">No customized rules added yet.</td></tr>
            {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- SHORTCUTS -->
    <div id="sec-shortcuts" class="section">
      <div class="page-header">
        <h1>Keyboard Shortcuts</h1>
        <p>Global triggers active across the entire operating system environment.</p>
      </div>
      <div class="shortcut-grid" style="grid-template-columns:1fr;gap:20px">
        <div class="shortcut-card" style="background:var(--bg-card)">
          <div>
            <div class="shortcut-keys"><kbd>Ctrl</kbd><span>+</span><kbd>Win</kbd></div>
            <div class="card-title" style="margin-bottom:8px">Push-to-Talk (Hold)</div>
            <div class="shortcut-desc">Press and hold these keys down. Speak normally. The moment you release both keys, recording stops, Whisper processes it, and the text is pasted immediately into the active text focus.</div>
          </div>
        </div>
        <div class="shortcut-card" style="background:var(--bg-card)">
          <div>
            <div class="shortcut-keys"><kbd>Ctrl</kbd><span>+</span><kbd>Win</kbd><span>+</span><kbd>Space</kbd></div>
            <div class="card-title" style="margin-bottom:8px">Toggle Recording State (Tap)</div>
            <div class="shortcut-desc">Tap once to begin recording. Tap again to terminate recording and perform automatic pasting. Ideal for hands-free speech.</div>
          </div>
        </div>
        <div class="shortcut-card" style="background:var(--bg-card)">
          <div>
            <div class="shortcut-keys"><kbd>Undo Pill</kbd></div>
            <div class="card-title" style="margin-bottom:8px">Undo &amp; Learn Corrections</div>
            <div class="shortcut-desc">When dictation completes, a small visual button saying "Undo &amp; Correct" appears for 4 seconds on top of all windows. Click it to undo typing and type the correct spelling so the AI learns the word.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- PREFERENCES -->
    <div id="sec-settings" class="section">
      <div class="page-header">
        <h1>Preferences</h1>
        <p>Manage application preferences and user configurations.</p>
      </div>
      
      {% if user %}
      <div class="card">
        <div class="card-title">Tone & Formatting Style</div>
        <div class="card-desc">Incorporate specific output styling guidelines for Whisper.</div>
        <form action="/update_settings" method="POST" style="display:flex;gap:16px;align-items:flex-end">
          <div style="flex:1">
            <label class="form-label">Active Tone</label>
            <select name="speaking_style">
              <option value="Casual" {{ 'selected' if settings.speaking_style == 'Casual' }}>Casual (Fluent, conversational style)</option>
              <option value="Formal" {{ 'selected' if settings.speaking_style == 'Formal' }}>Formal (Polished prose, punctuation-perfect)</option>
              <option value="Serious" {{ 'selected' if settings.speaking_style == 'Serious' }}>Serious (Highly direct, minimal phrasing)</option>
              <option value="Code" {{ 'selected' if settings.speaking_style == 'Code' }}>Code (Inline code blocks and variables)</option>
            </select>
          </div>
          <input type="hidden" name="theme" id="theme-input" value="{{ theme }}">
          <button type="submit" class="btn">Update Tone</button>
        </form>
      </div>
      {% else %}
      <div class="card" style="text-align:center;padding:48px">
        <p style="color:var(--text-muted);margin-bottom:20px;font-weight:500">Sign in using Google to customize active settings and tones.</p>
        <a href="/login" class="btn">Sign In</a>
      </div>
      {% endif %}
      
      <div class="card" style="border-color:rgba(244,63,94,0.2)">
        <div class="card-title" style="color:var(--danger)">Danger Actions</div>
        <div class="card-desc">Wipe all application data stored in the local SQLite database.</div>
        <form action="/clear_history" method="POST" onsubmit="return confirm('Wipe local database details completely?')">
          <button type="submit" class="btn btn-danger">Erase Local Database</button>
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
    user = session.get('user')
    settings = database.get_user_settings(user['email']) if user else {'speaking_style': 'Casual', 'theme': 'dark'}
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
        user=user, settings=settings, theme=theme,
        history=history, prompts=prompts, stats=stats,
        dictionary=dictionary, insight_label=insight_label, insight_score=insight_score)

@app.route('/login')
def login():
    if os.environ.get("GOOGLE_CLIENT_ID", "mock-client-id") == "mock-client-id":
        session['user'] = {"email": "localuser@localhost", "name": "Local User"}
        database.save_user("localuser@localhost", "Local User")
        return redirect('/')
    return google.authorize_redirect(url_for('authorize', _external=True))

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    session['user'] = user_info
    database.save_user(user_info['email'], user_info['name'])
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route("/update_settings", methods=["POST"])
def update_settings():
    user = session.get('user')
    if user:
        database.update_user_settings(user['email'], request.form.get("speaking_style"), request.form.get("theme", "dark"))
    return redirect(url_for("index"))

@app.route("/api/set_theme", methods=["POST"])
def set_theme_api():
    user = session.get('user')
    if user:
        data = request.get_json() or {}
        s = database.get_user_settings(user['email'])
        if s:
            database.update_user_settings(user['email'], s['speaking_style'], data.get('theme', 'dark'))
    return jsonify({"ok": True})

@app.route("/clear_history", methods=["POST"])
def clear_history():
    database.clear_history()
    audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "history_audio"))
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
    audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "history_audio"))
    return send_file(os.path.join(audio_dir, filename))

def run_server():
    database.init_db()
    os.makedirs(os.path.abspath(os.path.join(os.path.dirname(__file__), "history_audio")), exist_ok=True)
    app.run(host="127.0.0.1", port=2000, debug=False, use_reloader=False)

if __name__ == "__main__":
    run_server()
