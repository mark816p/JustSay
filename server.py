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
        return "No data yet", 0
    text = " ".join([h['transcript'] for h in history]).lower()
    words = text.split()
    if not words:
        return "No data yet", 0
    fillers = ['um', 'uh', 'like', 'you know', 'so']
    filler_count = sum(1 for w in words if w in fillers)
    avg_len = len(words) / len(history)
    score = int(min(100, max(0, 100 - (filler_count / max(len(words), 1)) * 300)))
    if filler_count > len(words) * 0.05:
        return "Hesitant Speaker", score
    elif avg_len > 20:
        return "Highly Descriptive", score
    elif avg_len < 5:
        return "Concise & Direct", score
    else:
        return "Balanced & Natural", score

HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="{{ theme }}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>JustSay</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root {
  --r: 14px;
  --accent: #7c5cfc;
  --accent2: #c084fc;
  --danger: #f43f5e;
  --success: #10b981;
  --trans: all .2s ease;
}
[data-theme=dark]{
  --bg: #0d0d14;
  --bg2: #13131f;
  --bg3: #1a1a2e;
  --border: rgba(255,255,255,.07);
  --text: #f0f0ff;
  --text2: rgba(240,240,255,.55);
  --card: rgba(255,255,255,.04);
  --card-hover: rgba(255,255,255,.07);
  --shadow: 0 8px 32px rgba(0,0,0,.4);
  --glow: rgba(124,92,252,.15);
}
[data-theme=light]{
  --bg: #f4f4f8;
  --bg2: #eeeef5;
  --bg3: #e8e8f0;
  --border: rgba(0,0,0,.08);
  --text: #0d0d1a;
  --text2: rgba(13,13,26,.5);
  --card: rgba(255,255,255,.7);
  --card-hover: rgba(255,255,255,.9);
  --shadow: 0 4px 20px rgba(0,0,0,.08);
  --glow: rgba(124,92,252,.08);
}

html{font-size:16px}
body{
  font-family:'Inter',sans-serif;
  background:var(--bg);
  color:var(--text);
  min-height:100vh;
  transition:background .3s,color .3s;
  -webkit-font-smoothing:antialiased;
}

/* SIDEBAR LAYOUT */
.layout{display:flex;min-height:100vh}

.sidebar{
  width:240px;min-width:240px;
  background:var(--bg2);
  border-right:1px solid var(--border);
  display:flex;flex-direction:column;
  padding:28px 0;
  position:sticky;top:0;height:100vh;
  overflow-y:auto;
}

.sidebar-logo{
  padding:0 24px 28px;
  border-bottom:1px solid var(--border);
  margin-bottom:20px;
}
.sidebar-logo .logo-text{
  font-size:1.5rem;font-weight:700;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
}
.sidebar-logo .logo-sub{font-size:.72rem;color:var(--text2);margin-top:2px;letter-spacing:.5px;text-transform:uppercase;}

.nav-item{
  display:flex;align-items:center;gap:12px;
  padding:11px 24px;font-size:.88rem;font-weight:500;
  color:var(--text2);cursor:pointer;
  border-left:3px solid transparent;
  transition:var(--trans);text-decoration:none;
}
.nav-item:hover,.nav-item.active{
  color:var(--text);
  background:var(--card);
  border-left-color:var(--accent);
}
.nav-item svg{width:18px;height:18px;flex-shrink:0;opacity:.7}
.nav-item:hover svg,.nav-item.active svg{opacity:1}

.nav-section-title{
  font-size:.68rem;font-weight:600;letter-spacing:.8px;
  text-transform:uppercase;color:var(--text2);
  padding:16px 24px 6px;
}

.sidebar-bottom{
  margin-top:auto;padding:20px 24px 0;
  border-top:1px solid var(--border);
}
.theme-btn{
  display:flex;align-items:center;gap:10px;
  background:var(--card);border:1px solid var(--border);
  border-radius:10px;padding:10px 14px;
  cursor:pointer;font-size:.85rem;font-weight:500;
  color:var(--text);width:100%;transition:var(--trans);
}
.theme-btn:hover{background:var(--card-hover)}

/* MAIN CONTENT */
.main{flex:1;padding:40px 48px;overflow-y:auto;max-width:960px}

.page-header{margin-bottom:36px}
.page-header h1{font-size:1.8rem;font-weight:700;margin-bottom:6px}
.page-header p{color:var(--text2);font-size:.9rem}

/* STAT CARDS */
.stats-row{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px}
.stat-card{
  background:var(--card);border:1px solid var(--border);
  border-radius:var(--r);padding:24px;
  transition:var(--trans);position:relative;overflow:hidden;
}
.stat-card::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(circle at top right,var(--glow),transparent 70%);
  pointer-events:none;
}
.stat-card:hover{background:var(--card-hover);box-shadow:var(--shadow)}
.stat-label{font-size:.75rem;font-weight:600;letter-spacing:.5px;text-transform:uppercase;color:var(--text2);margin-bottom:10px}
.stat-value{font-size:2.4rem;font-weight:700;line-height:1;margin-bottom:4px}
.stat-value.accent{background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.stat-sub{font-size:.8rem;color:var(--text2)}

/* CARDS */
.card{
  background:var(--card);border:1px solid var(--border);
  border-radius:var(--r);padding:28px;
  margin-bottom:20px;transition:var(--trans);
}
.card:hover{background:var(--card-hover)}
.card-title{font-size:1rem;font-weight:600;margin-bottom:4px}
.card-desc{font-size:.82rem;color:var(--text2);margin-bottom:20px}

/* INPUTS */
input[type=text],select,textarea{
  background:var(--bg3);
  border:1px solid var(--border);
  border-radius:9px;padding:10px 14px;
  color:var(--text);font-family:'Inter',sans-serif;
  font-size:.88rem;width:100%;
  transition:var(--trans);outline:none;
}
input[type=text]:focus,select:focus,textarea:focus{
  border-color:var(--accent);
  box-shadow:0 0 0 3px rgba(124,92,252,.15);
}
select option{background:var(--bg2)}

/* BUTTONS */
.btn{
  display:inline-flex;align-items:center;gap:8px;
  background:var(--accent);color:#fff;
  border:none;border-radius:9px;padding:10px 20px;
  font-size:.88rem;font-weight:600;cursor:pointer;
  font-family:'Inter',sans-serif;transition:var(--trans);
  text-decoration:none;white-space:nowrap;
}
.btn:hover{filter:brightness(1.15);transform:translateY(-1px)}
.btn:active{transform:translateY(0)}
.btn-sm{padding:7px 14px;font-size:.8rem;border-radius:7px}
.btn-ghost{background:transparent;border:1px solid var(--border);color:var(--text)}
.btn-ghost:hover{background:var(--card-hover);filter:none}
.btn-danger{background:var(--danger)}
.btn-success{background:var(--success)}
.btn-outline-accent{background:transparent;border:1px solid var(--accent);color:var(--accent)}
.btn-outline-accent:hover{background:var(--accent);color:#fff;filter:none}

/* INLINE FORM ROW */
.form-row{display:flex;gap:12px;align-items:center}
.form-row input{flex:1}
.form-group{margin-bottom:16px}
.form-label{display:block;font-size:.8rem;font-weight:600;color:var(--text2);margin-bottom:6px;letter-spacing:.3px}

/* TABLE */
.table-wrap{overflow-x:auto;margin-top:12px}
table{width:100%;border-collapse:collapse}
th{text-align:left;font-size:.72rem;font-weight:600;letter-spacing:.5px;text-transform:uppercase;color:var(--text2);padding:10px 14px;border-bottom:1px solid var(--border)}
td{padding:12px 14px;font-size:.85rem;border-bottom:1px solid var(--border);vertical-align:middle}
tr:last-child td{border-bottom:none}
tr:hover td{background:var(--card)}

/* BADGES */
.badge{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:20px;font-size:.75rem;font-weight:600}
.badge-active{background:rgba(16,185,129,.12);color:#10b981}
.badge-accent{background:rgba(124,92,252,.12);color:var(--accent)}

/* TAGS */
.tags{display:flex;flex-wrap:wrap;gap:8px}
.tag{background:rgba(124,92,252,.1);color:var(--accent);border:1px solid rgba(124,92,252,.2);padding:5px 12px;border-radius:20px;font-size:.8rem;font-weight:500}

/* SHORTCUT KEY DISPLAY */
.shortcut-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.shortcut-card{
  background:var(--bg3);border:1px solid var(--border);
  border-radius:10px;padding:16px 18px;
  display:flex;align-items:flex-start;gap:14px;
}
.shortcut-keys{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:8px}
kbd{
  background:var(--bg2);border:1px solid var(--border);
  border-bottom:3px solid var(--border);
  border-radius:6px;padding:4px 9px;
  font-family:'Inter',sans-serif;font-size:.78rem;font-weight:600;color:var(--text);
}
.shortcut-desc{font-size:.8rem;color:var(--text2)}

/* AUDIO PLAYER */
audio{height:34px;width:100%;filter:hue-rotate(240deg)}

/* PRIVACY BANNER */
.privacy-banner{
  display:flex;align-items:center;gap:10px;
  background:rgba(16,185,129,.07);border:1px solid rgba(16,185,129,.15);
  border-radius:10px;padding:12px 16px;margin-bottom:20px;
  font-size:.82rem;color:var(--text2);
}

/* PROGRESS BAR */
.progress-bar{background:var(--bg3);border-radius:99px;height:8px;margin-top:8px;overflow:hidden}
.progress-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,var(--accent),var(--accent2))}

/* USER CHIP */
.user-chip{display:flex;align-items:center;gap:10px;padding:12px 24px 20px;border-bottom:1px solid var(--border);margin-bottom:10px}
.user-avatar{width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.9rem;color:#fff;flex-shrink:0}
.user-name{font-size:.85rem;font-weight:600;line-height:1.2}
.user-email{font-size:.72rem;color:var(--text2)}

/* SECTION HIDDEN BY DEFAULT */
.section{display:none}
.section.active{display:block}

/* SCROLLBAR */
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:99px}
</style>
</head>
<body>

<div class="layout">
  <!-- SIDEBAR -->
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="logo-text">JustSay</div>
      <div class="logo-sub">Voice AI · Local</div>
    </div>

    {% if user %}
    <div class="user-chip">
      <div class="user-avatar">{{ user.name[0].upper() }}</div>
      <div>
        <div class="user-name">{{ user.name }}</div>
        <div class="user-email">{{ user.email }}</div>
      </div>
    </div>
    {% endif %}

    <span class="nav-section-title">Main</span>
    <a class="nav-item active" onclick="showSection('overview',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
      Overview
    </a>
    <a class="nav-item" onclick="showSection('history',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
      History
    </a>
    <a class="nav-item" onclick="showSection('dictionary',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
      Dictionary
    </a>
    <a class="nav-item" onclick="showSection('prompts',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      Instructions
    </a>

    <span class="nav-section-title">System</span>
    <a class="nav-item" onclick="showSection('shortcuts',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M8 14h8"/></svg>
      Shortcuts
    </a>
    <a class="nav-item" onclick="showSection('settings',this)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      Settings
    </a>

    <div class="sidebar-bottom">
      {% if user %}
        <a href="/logout" class="btn btn-ghost" style="width:100%;justify-content:center;margin-bottom:10px">Sign Out</a>
      {% else %}
        <a href="/login" class="btn" style="width:100%;justify-content:center;margin-bottom:10px">Login with Google</a>
      {% endif %}
      <button class="theme-btn" onclick="toggleTheme()">
        <span id="theme-icon">{{ "🌙" if theme == "dark" else "☀️" }}</span>
        <span id="theme-label">{{ "Dark Mode" if theme == "dark" else "Light Mode" }}</span>
      </button>
    </div>
  </aside>

  <!-- MAIN -->
  <main class="main">

    <!-- OVERVIEW -->
    <div id="sec-overview" class="section active">
      <div class="page-header">
        <h1>Overview</h1>
        <p>Your voice activity and insights at a glance.</p>
      </div>
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-label">Dictations</div>
          <div class="stat-value accent">{{ stats.total_dictations }}</div>
          <div class="stat-sub">Total sessions</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Words Spoken</div>
          <div class="stat-value accent">{{ stats.total_words }}</div>
          <div class="stat-sub">Across all sessions</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Speaking Style</div>
          <div class="stat-value" style="font-size:1.3rem;padding-top:6px;">{{ insight_label }}</div>
          <div class="stat-sub">Fluency score</div>
          <div class="progress-bar"><div class="progress-fill" style="width:{{ insight_score }}%"></div></div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">How to Use</div>
        <div class="card-desc">Your keyboard shortcuts are active whenever JustSay is running in the tray.</div>
        <div class="shortcut-grid">
          <div class="shortcut-card">
            <div>
              <div class="shortcut-keys"><kbd>Ctrl</kbd><span>+</span><kbd>Win</kbd></div>
              <div class="card-title" style="font-size:.88rem">Push-to-Talk</div>
              <div class="shortcut-desc">Hold to record. Releases when you let go.</div>
            </div>
          </div>
          <div class="shortcut-card">
            <div>
              <div class="shortcut-keys"><kbd>Ctrl</kbd><span>+</span><kbd>Win</kbd><span>+</span><kbd>Space</kbd></div>
              <div class="card-title" style="font-size:.88rem">Toggle Record</div>
              <div class="shortcut-desc">Press once to start, press again to stop and transcribe.</div>
            </div>
          </div>
        </div>
      </div>

      <div class="privacy-banner">
        🔒 <strong>100% Private.</strong>&nbsp;All audio and transcripts are processed and stored exclusively on your machine. Nothing is sent to any server.
      </div>
    </div>

    <!-- HISTORY -->
    <div id="sec-history" class="section">
      <div class="page-header">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
          <div>
            <h1>History</h1>
            <p>All of your past dictation sessions, stored locally.</p>
          </div>
          <form action="/clear_history" method="POST" onsubmit="return confirm('Permanently delete all local history?')">
            <button type="submit" class="btn btn-danger btn-sm">Wipe All Data</button>
          </form>
        </div>
      </div>
      <div class="privacy-banner">
        🔒 Audio and transcripts never leave your device. Deletion is permanent and immediate.
      </div>
      <div class="card" style="padding:0;overflow:hidden">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Time</th><th>Transcript</th><th>Words</th><th>Playback</th></tr></thead>
            <tbody>
            {% for h in history %}
            <tr>
              <td style="white-space:nowrap;color:var(--text2);font-size:.78rem">{{ h.timestamp }}</td>
              <td style="max-width:340px">{{ h.transcript }}</td>
              <td><span class="badge badge-accent">{{ h.word_count }}</span></td>
              <td><audio controls><source src="/audio/{{ h.audio_filename }}" type="audio/wav"></audio></td>
            </tr>
            {% else %}
            <tr><td colspan="4" style="text-align:center;padding:40px;color:var(--text2)">No history yet. Start dictating!</td></tr>
            {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- DICTIONARY -->
    <div id="sec-dictionary" class="section">
      <div class="page-header">
        <h1>Learned Dictionary</h1>
        <p>Custom words and names the AI prioritises. Added automatically when you use Undo &amp; Correct.</p>
      </div>
      <div class="card">
        <div class="card-title">Your Words</div>
        <div class="card-desc">These terms are fed directly into the transcription engine to improve accuracy.</div>
        <div class="tags">
          {% for word in dictionary %}
            <span class="tag">{{ word }}</span>
          {% else %}
            <span style="color:var(--text2);font-size:.85rem;font-style:italic">Empty. After dictating, use the Undo &amp; Correct pop-up to teach JustSay new words.</span>
          {% endfor %}
        </div>
      </div>
    </div>

    <!-- PROMPTS / INSTRUCTIONS -->
    <div id="sec-prompts" class="section">
      <div class="page-header">
        <h1>Custom Instructions</h1>
        <p>Tell the AI how to format your transcriptions. One rule is active at a time.</p>
      </div>
      <div class="card">
        <form action="/add_prompt" method="POST" class="form-row">
          <input type="text" name="prompt_text" placeholder="e.g. Always capitalise product names. Use Markdown for code.">
          <button type="submit" class="btn">Add Rule</button>
        </form>
      </div>
      <div class="card" style="padding:0;overflow:hidden">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Status</th><th>Rule</th><th style="text-align:right">Actions</th></tr></thead>
            <tbody>
            {% for p in prompts %}
            <tr>
              <td>
                {% if p.is_active %}<span class="badge badge-active">● Active</span>
                {% else %}<a href="/set_active/{{ p.id }}" class="btn btn-sm btn-outline-accent">Activate</a>{% endif %}
              </td>
              <td>{{ p.prompt_text }}</td>
              <td style="text-align:right"><a href="/delete_prompt/{{ p.id }}" class="btn btn-sm btn-ghost" style="color:var(--danger);border-color:var(--danger)">Delete</a></td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="text-align:center;padding:40px;color:var(--text2)">No rules yet.</td></tr>
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
        <p>Global hotkeys — work in any application while JustSay is running.</p>
      </div>
      <div class="shortcut-grid" style="grid-template-columns:1fr">
        <div class="shortcut-card">
          <div>
            <div class="shortcut-keys"><kbd>Ctrl</kbd><span>+</span><kbd>⊞ Win</kbd></div>
            <div class="card-title" style="margin-bottom:6px">Push-to-Talk</div>
            <div class="shortcut-desc">Hold the keys to record. The moment you release, JustSay transcribes and types the text into your active application.</div>
          </div>
        </div>
        <div class="shortcut-card" style="margin-top:14px">
          <div>
            <div class="shortcut-keys"><kbd>Ctrl</kbd><span>+</span><kbd>⊞ Win</kbd><span>+</span><kbd>Space</kbd></div>
            <div class="card-title" style="margin-bottom:6px">Toggle Recording</div>
            <div class="shortcut-desc">Press once to start recording. Press again to stop. Ideal for longer dictations where you don't want to hold the keys.</div>
          </div>
        </div>
        <div class="shortcut-card" style="margin-top:14px">
          <div>
            <div class="shortcut-keys"><kbd>Undo Popup</kbd></div>
            <div class="card-title" style="margin-bottom:6px">Undo &amp; Correct (on-screen)</div>
            <div class="shortcut-desc">After every transcription, a 4-second floating pill appears. Click "Undo &amp; Correct" to revert the paste and teach JustSay the correct word.</div>
          </div>
        </div>
      </div>
    </div>

    <!-- SETTINGS -->
    <div id="sec-settings" class="section">
      <div class="page-header">
        <h1>Settings</h1>
        <p>Configure your transcription preferences.</p>
      </div>
      {% if user %}
      <div class="card">
        <div class="card-title">Speaking Style</div>
        <div class="card-desc">Controls how the AI formats your transcriptions.</div>
        <form action="/update_settings" method="POST" style="display:flex;gap:12px;align-items:flex-end">
          <div style="flex:1">
            <label class="form-label">Tone</label>
            <select name="speaking_style">
              <option value="Casual" {{ 'selected' if settings.speaking_style == 'Casual' }}>Casual (relaxed, natural)</option>
              <option value="Formal" {{ 'selected' if settings.speaking_style == 'Formal' }}>Formal (polished, professional)</option>
              <option value="Serious" {{ 'selected' if settings.speaking_style == 'Serious' }}>Serious (direct, concise)</option>
              <option value="Code" {{ 'selected' if settings.speaking_style == 'Code' }}>Code / Technical</option>
            </select>
          </div>
          <input type="hidden" name="theme" id="theme-input" value="{{ theme }}">
          <button type="submit" class="btn">Save</button>
        </form>
      </div>
      {% else %}
      <div class="card" style="text-align:center;padding:40px">
        <p style="color:var(--text2);margin-bottom:16px">Sign in to save personal preferences.</p>
        <a href="/login" class="btn">Login with Google</a>
      </div>
      {% endif %}
      <div class="card">
        <div class="card-title">Danger Zone</div>
        <div class="card-desc">Permanently removes all local dictation data. This cannot be undone.</div>
        <form action="/clear_history" method="POST" onsubmit="return confirm('Delete all local history permanently?')">
          <button type="submit" class="btn btn-danger">Wipe All Data</button>
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
  document.getElementById('theme-label').textContent = next === 'dark' ? 'Dark Mode' : 'Light Mode';
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
