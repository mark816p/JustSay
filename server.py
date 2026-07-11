from flask import Flask, render_template_string, request, redirect, url_for, send_file, session
from authlib.integrations.flask_client import OAuth
import database
import os
import re

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-local-key")

# OAuth Setup
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>JustSay - Dashboard</title>
    <style>
        :root {
            --bg-color: {% if theme == 'Dark' %}#121212{% else %}#f5f5f5{% endif %};
            --text-color: {% if theme == 'Dark' %}#ffffff{% else %}#333333{% endif %};
            --section-bg: {% if theme == 'Dark' %}#1e1e1e{% else %}#ffffff{% endif %};
            --border-color: {% if theme == 'Dark' %}#333{% else %}#ccc{% endif %};
            --accent: #bb86fc;
            --danger: #cf6679;
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: var(--bg-color); color: var(--text-color); margin: 0; padding: 20px; }
        h1, h2 { color: var(--accent); }
        .section { background-color: var(--section-bg); padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid var(--border-color); }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid var(--border-color); padding: 10px; text-align: left; }
        th { background-color: {% if theme == 'Dark' %}#2c2c2c{% else %}#e0e0e0{% endif %}; }
        input[type="text"], select { width: 80%; padding: 8px; background-color: var(--bg-color); color: var(--text-color); border: 1px solid var(--border-color); border-radius: 5px; }
        button { background-color: var(--accent); color: #000; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { opacity: 0.8; }
        .btn-danger { background-color: var(--danger); color: white; }
        .header { display: flex; justify-content: space-between; align-items: center; }
        .audio-player { width: 250px; height: 30px; }
        .stats-box { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-card { background-color: var(--section-bg); padding: 20px; border-radius: 10px; border: 1px solid var(--border-color); flex: 1; text-align: center; }
        .stat-card h3 { margin: 0; font-size: 24px; color: var(--accent); }
    </style>
</head>
<body>
    <div class="header">
        <h1>JustSay Dashboard</h1>
        <div>
            {% if user %}
                <span>Welcome, {{ user.name }}!</span>
                <a href="/logout" style="color: var(--accent); margin-left: 15px;">Logout</a>
            {% else %}
                <a href="/login" style="color: var(--accent);">Login with Google</a>
            {% endif %}
        </div>
    </div>
    
    {% if user %}
    <div class="section">
        <h2>Settings & Onboarding</h2>
        <form action="/update_settings" method="POST">
            <label>Speaking Style:</label>
            <select name="speaking_style">
                <option value="Casual" {% if settings.speaking_style == 'Casual' %}selected{% endif %}>Casual</option>
                <option value="Formal" {% if settings.speaking_style == 'Formal' %}selected{% endif %}>Formal</option>
                <option value="Serious" {% if settings.speaking_style == 'Serious' %}selected{% endif %}>Serious</option>
                <option value="Code" {% if settings.speaking_style == 'Code' %}selected{% endif %}>Code / Developer</option>
            </select>
            <br><br>
            <label>Theme:</label>
            <select name="theme">
                <option value="Dark" {% if settings.theme == 'Dark' %}selected{% endif %}>Dark</option>
                <option value="Light" {% if settings.theme == 'Light' %}selected{% endif %}>Light</option>
            </select>
            <br><br>
            <button type="submit">Save Settings</button>
        </form>
    </div>
    {% endif %}

    <div class="stats-box">
        <div class="stat-card">
            <h3>{{ stats.total_dictations }}</h3>
            <p>Total Dictations</p>
        </div>
        <div class="stat-card">
            <h3>{{ stats.total_words }}</h3>
            <p>Words Dictated</p>
        </div>
        <div class="stat-card">
            <h3>{{ insights }}</h3>
            <p>Speaking Style Insights</p>
        </div>
    </div>
    
    <div class="section">
        <h2>Auto-Dictionary</h2>
        <p>Words added to your dictionary via the Undo pop-up will appear here. Whisper will learn to prioritize these words.</p>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            {% for word in dictionary %}
                <span style="background-color: var(--accent); color: black; padding: 5px 10px; border-radius: 15px;">{{ word }}</span>
            {% else %}
                <span style="color: #888;">Dictionary is empty. Make corrections using the Undo pop-up!</span>
            {% endfor %}
        </div>
    </div>

    <div class="section">
        <h2>Custom Prompts</h2>
        <form action="/add_prompt" method="POST">
            <input type="text" name="prompt_text" placeholder="Enter a new prompt for the AI..." required>
            <button type="submit">Add Prompt</button>
        </form>
        <table>
            <tr>
                <th>Active</th>
                <th>Prompt Text</th>
                <th>Actions</th>
            </tr>
            {% for p in prompts %}
            <tr>
                <td>{% if p.is_active %}⭐ Active{% else %}<a href="/set_active/{{ p.id }}" style="color: var(--accent);">Set Active</a>{% endif %}</td>
                <td>{{ p.prompt_text }}</td>
                <td><a href="/delete_prompt/{{ p.id }}" style="color: var(--danger);">Delete</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="section">
        <div class="header">
            <h2>Dictation History</h2>
            <form action="/clear_history" method="POST" onsubmit="return confirm('Are you sure you want to permanently delete all local history? This data never leaves your device.');">
                <button type="submit" class="btn-danger">Clear All History</button>
            </form>
        </div>
        <p style="color: #888; font-size: 12px;">🔒 All audio and transcripts are stored purely on your local device. No data is sent to the cloud.</p>
        <table>
            <tr>
                <th>Date / Time</th>
                <th>Transcript</th>
                <th>Words</th>
                <th>Audio</th>
            </tr>
            {% for h in history %}
            <tr>
                <td>{{ h.timestamp }}</td>
                <td>{{ h.transcript }}</td>
                <td>{{ h.word_count }}</td>
                <td>
                    <audio class="audio-player" controls>
                        <source src="/audio/{{ h.audio_path.split('/')[-1] if '/' in h.audio_path else h.audio_path.split('\\')[-1] }}" type="audio/wav">
                    </audio>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

def generate_insights(history):
    if not history:
        return "Not enough data"
    
    text = " ".join([h['transcript'] for h in history]).lower()
    words = text.split()
    if not words:
        return "Not enough data"
    
    fillers = ['um', 'uh', 'like', 'you know', 'so']
    filler_count = sum(1 for w in words if w in fillers)
    
    avg_length = len(words) / len(history)
    
    if filler_count > len(words) * 0.05:
        return "Hesitant (Many fillers)"
    elif avg_length > 20:
        return "Highly Descriptive"
    elif avg_length < 5:
        return "Concise / Short-spoken"
    else:
        return "Balanced & Natural"

@app.route("/")
def index():
    user = session.get('user')
    settings = database.get_user_settings(user['email']) if user else {'speaking_style': 'Casual', 'theme': 'Dark'}
    
    prompts = database.get_all_prompts()
    history = database.get_history()
    stats = database.get_statistics()
    dictionary = database.get_dictionary()
    insights = generate_insights(history)
    
    return render_template_string(HTML_TEMPLATE, user=user, settings=settings, prompts=prompts, history=history, stats=stats, dictionary=dictionary, insights=insights, theme=settings['theme'])

@app.route('/login')
def login():
    if os.environ.get("GOOGLE_CLIENT_ID") == "mock-client-id":
        # Mock login if no keys provided (as per local-first instructions)
        session['user'] = {"email": "localuser@localhost", "name": "Local User"}
        database.save_user("localuser@localhost", "Local User")
        return redirect('/')
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
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
        style = request.form.get("speaking_style")
        theme = request.form.get("theme")
        database.update_user_settings(user['email'], style, theme)
    return redirect(url_for("index"))

@app.route("/clear_history", methods=["POST"])
def clear_history():
    database.clear_history()
    # Also delete files locally
    audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "history_audio"))
    for f in os.listdir(audio_dir):
        os.remove(os.path.join(audio_dir, f))
    return redirect(url_for("index"))

@app.route("/add_prompt", methods=["POST"])
def add_prompt():
    text = request.form.get("prompt_text")
    if text:
        database.add_prompt(text)
    return redirect(url_for("index"))

@app.route("/set_active/<int:prompt_id>")
def set_active(prompt_id):
    database.set_active_prompt(prompt_id)
    return redirect(url_for("index"))

@app.route("/delete_prompt/<int:prompt_id>")
def delete_prompt(prompt_id):
    database.delete_prompt(prompt_id)
    return redirect(url_for("index"))

@app.route("/audio/<filename>")
def get_audio(filename):
    audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "history_audio"))
    return send_file(os.path.join(audio_dir, filename))

def run_server():
    database.init_db()
    audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "history_audio"))
    os.makedirs(audio_dir, exist_ok=True)
    app.run(host="127.0.0.1", port=2000, debug=False, use_reloader=False)

if __name__ == "__main__":
    run_server()
