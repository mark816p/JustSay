from flask import Flask, render_template_string, request, redirect, url_for, send_file, session, jsonify
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
<html lang="en" data-theme="{{ settings.theme.lower() }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JustSay - Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Light Theme Tokens */
            --bg-color-light: #f8fafc;
            --text-color-light: #1e293b;
            --card-bg-light: rgba(255, 255, 255, 0.7);
            --border-light: rgba(226, 232, 240, 0.8);
            --gradient-light: linear-gradient(135deg, #e0e7ff 0%, #f3e8ff 100%);
            
            /* Dark Theme Tokens */
            --bg-color-dark: #0f172a;
            --text-color-dark: #f8fafc;
            --card-bg-dark: rgba(30, 41, 59, 0.7);
            --border-dark: rgba(51, 65, 85, 0.8);
            --gradient-dark: linear-gradient(135deg, #1e1b4b 0%, #2e1065 100%);

            /* Universal / Accents */
            --accent-primary: #8b5cf6;
            --accent-hover: #7c3aed;
            --danger: #ef4444;
            --danger-hover: #dc2626;
            --glass-blur: blur(12px);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        html[data-theme='light'] {
            --bg-color: var(--bg-color-light);
            --text-color: var(--text-color-light);
            --card-bg: var(--card-bg-light);
            --border: var(--border-light);
            --gradient: var(--gradient-light);
        }

        html[data-theme='dark'] {
            --bg-color: var(--bg-color-dark);
            --text-color: var(--text-color-dark);
            --card-bg: var(--card-bg-dark);
            --border: var(--border-dark);
            --gradient: var(--gradient-dark);
        }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--gradient);
            background-color: var(--bg-color);
            background-attachment: fixed;
            color: var(--text-color);
            margin: 0;
            padding: 40px 20px;
            min-height: 100vh;
            transition: var(--transition);
        }

        h1, h2, h3 {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            color: var(--text-color);
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
        }

        /* Glassmorphism Card Base */
        .glass-card {
            background: var(--card-bg);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.1);
            transition: var(--transition);
        }

        .glass-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.2);
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 2.5rem;
            margin: 0;
            background: linear-gradient(to right, var(--accent-primary), #d946ef);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-box {
            text-align: center;
            padding: 30px;
        }

        .stat-box h3 {
            font-size: 3rem;
            margin: 0 0 10px 0;
            color: var(--accent-primary);
        }

        .stat-box p {
            margin: 0;
            font-size: 1.1rem;
            font-weight: 500;
            opacity: 0.8;
        }

        /* Forms & Inputs */
        input[type="text"], select {
            width: 100%;
            padding: 12px 15px;
            background: rgba(0,0,0,0.05);
            color: var(--text-color);
            border: 1px solid var(--border);
            border-radius: 10px;
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            margin-bottom: 15px;
            box-sizing: border-box;
            transition: var(--transition);
        }
        
        html[data-theme='dark'] input[type="text"], html[data-theme='dark'] select {
            background: rgba(255,255,255,0.05);
        }

        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
        }

        /* Buttons */
        button, .btn {
            background: var(--accent-primary);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 10px;
            cursor: pointer;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 1rem;
            transition: var(--transition);
            text-decoration: none;
            display: inline-block;
        }

        button:hover, .btn:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
        }

        .btn-danger { background: var(--danger); }
        .btn-danger:hover { background: var(--danger-hover); }

        /* Tables */
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0 10px;
        }

        th, td {
            padding: 15px;
            text-align: left;
        }

        th {
            font-weight: 600;
            opacity: 0.8;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        tr td {
            background: rgba(0,0,0,0.02);
        }
        html[data-theme='dark'] tr td {
            background: rgba(255,255,255,0.02);
        }

        tr td:first-child { border-top-left-radius: 10px; border-bottom-left-radius: 10px; }
        tr td:last-child { border-top-right-radius: 10px; border-bottom-right-radius: 10px; }

        /* Tags */
        .tag {
            background: rgba(139, 92, 246, 0.15);
            color: var(--accent-primary);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            display: inline-block;
            margin: 4px;
        }
        
        .toggle-container {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>JustSay</h1>
            <div style="display: flex; gap: 20px; align-items: center;">
                <div class="toggle-container" onclick="toggleTheme()">
                    <span style="font-size: 1.2rem;" id="theme-icon">{% if settings.theme.lower() == 'dark' %}🌙{% else %}☀️{% endif %}</span>
                </div>
                {% if user %}
                    <span style="font-weight: 500;">{{ user.name }}</span>
                    <a href="/logout" class="btn" style="padding: 8px 16px;">Logout</a>
                {% else %}
                    <a href="/login" class="btn">Login</a>
                {% endif %}
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="glass-card stat-box">
                <h3>{{ stats.total_dictations }}</h3>
                <p>Total Dictations</p>
            </div>
            <div class="glass-card stat-box">
                <h3>{{ stats.total_words }}</h3>
                <p>Words Dictated</p>
            </div>
            <div class="glass-card stat-box">
                <h3 style="font-size: 1.8rem; margin-top: 15px;">{{ insights }}</h3>
                <p>Speaking Style</p>
            </div>
        </div>

        {% if user %}
        <div class="glass-card">
            <h2>Settings & Preferences</h2>
            <form action="/update_settings" method="POST" style="display: flex; gap: 20px; align-items: flex-end;">
                <div style="flex: 1;">
                    <label style="display: block; margin-bottom: 8px; font-weight: 500;">Tone / Style</label>
                    <select name="speaking_style" style="margin-bottom: 0;">
                        <option value="Casual" {% if settings.speaking_style == 'Casual' %}selected{% endif %}>Casual</option>
                        <option value="Formal" {% if settings.speaking_style == 'Formal' %}selected{% endif %}>Formal</option>
                        <option value="Serious" {% if settings.speaking_style == 'Serious' %}selected{% endif %}>Serious</option>
                        <option value="Code" {% if settings.speaking_style == 'Code' %}selected{% endif %}>Code / Developer</option>
                    </select>
                </div>
                <input type="hidden" name="theme" id="theme-input" value="{{ settings.theme }}">
                <button type="submit">Save Preferences</button>
            </form>
        </div>
        {% endif %}

        <div class="glass-card">
            <h2>Learned Dictionary</h2>
            <p style="opacity: 0.8; margin-bottom: 20px;">Words added via the quick Undo pop-up. The AI prioritizes these terms during dictation.</p>
            <div>
                {% for word in dictionary %}
                    <span class="tag">{{ word }}</span>
                {% else %}
                    <span style="opacity: 0.6; font-style: italic;">Your dictionary is empty. Correct words after dictating to train JustSay!</span>
                {% endfor %}
            </div>
        </div>

        <div class="glass-card">
            <h2>Custom Instructions</h2>
            <form action="/add_prompt" method="POST" style="display: flex; gap: 15px; margin-bottom: 20px;">
                <input type="text" name="prompt_text" placeholder="E.g. Format code with Markdown blocks, capitalize Product names..." required style="margin-bottom: 0;">
                <button type="submit" style="white-space: nowrap;">Add Rule</button>
            </form>
            <table>
                <tr>
                    <th>Status</th>
                    <th>Instruction Text</th>
                    <th style="text-align: right;">Action</th>
                </tr>
                {% for p in prompts %}
                <tr>
                    <td style="width: 120px;">
                        {% if p.is_active %}
                            <span class="tag" style="background: rgba(34, 197, 94, 0.15); color: #22c55e;">Active</span>
                        {% else %}
                            <a href="/set_active/{{ p.id }}" style="color: var(--accent-primary); text-decoration: none; font-weight: 500;">Activate</a>
                        {% endif %}
                    </td>
                    <td>{{ p.prompt_text }}</td>
                    <td style="text-align: right;"><a href="/delete_prompt/{{ p.id }}" style="color: var(--danger); text-decoration: none; font-weight: 500;">Delete</a></td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="glass-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2>Local History</h2>
                <form action="/clear_history" method="POST" onsubmit="return confirm('Permanently delete all local data?');">
                    <button type="submit" class="btn-danger">Wipe Data</button>
                </form>
            </div>
            <p style="opacity: 0.7; font-size: 0.9rem; margin-top: -10px;">🔒 Processed entirely on-device. No audio or text leaves your machine.</p>
            <table>
                <tr>
                    <th>Time</th>
                    <th>Transcript</th>
                    <th>Audio</th>
                </tr>
                {% for h in history %}
                <tr>
                    <td style="white-space: nowrap; font-size: 0.9rem; opacity: 0.8;">{{ h.timestamp }}</td>
                    <td style="line-height: 1.5;">{{ h.transcript }}</td>
                    <td style="width: 250px;">
                        <audio controls style="height: 35px; width: 100%; outline: none;">
                            <source src="/audio/{{ h.audio_path.split('/')[-1] if '/' in h.audio_path else h.audio_path.split('\\')[-1] }}" type="audio/wav">
                        </audio>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>

    <script>
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            document.getElementById('theme-icon').innerText = newTheme === 'dark' ? '🌙' : '☀️';
            document.getElementById('theme-input').value = newTheme.charAt(0).toUpperCase() + newTheme.slice(1);
            
            // Optionally auto-save theme via fetch if desired
            fetch('/api/set_theme', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ theme: newTheme.charAt(0).toUpperCase() + newTheme.slice(1) })
            });
        }
    </script>
</body>
</html>
"""

def generate_insights(history):
    if not history:
        return "Learning..."
    
    text = " ".join([h['transcript'] for h in history]).lower()
    words = text.split()
    if not words:
        return "Learning..."
    
    fillers = ['um', 'uh', 'like', 'you know', 'so']
    filler_count = sum(1 for w in words if w in fillers)
    
    avg_length = len(words) / len(history)
    
    if filler_count > len(words) * 0.05:
        return "Hesitant"
    elif avg_length > 20:
        return "Descriptive"
    elif avg_length < 5:
        return "Concise"
    else:
        return "Balanced"

@app.route("/")
def index():
    user = session.get('user')
    settings = database.get_user_settings(user['email']) if user else {'speaking_style': 'Casual', 'theme': 'Dark'}
    
    prompts = database.get_all_prompts()
    history = database.get_history()
    stats = database.get_statistics()
    dictionary = database.get_dictionary()
    insights = generate_insights(history)
    
    return render_template_string(HTML_TEMPLATE, user=user, settings=settings, prompts=prompts, history=history, stats=stats, dictionary=dictionary, insights=insights)

@app.route('/login')
def login():
    if os.environ.get("GOOGLE_CLIENT_ID") == "mock-client-id":
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

@app.route("/api/set_theme", methods=["POST"])
def set_theme_api():
    user = session.get('user')
    if user:
        data = request.get_json()
        theme = data.get('theme', 'Dark')
        settings = database.get_user_settings(user['email'])
        if settings:
            database.update_user_settings(user['email'], settings['speaking_style'], theme)
    return jsonify({"success": True})

@app.route("/clear_history", methods=["POST"])
def clear_history():
    database.clear_history()
    audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "history_audio"))
    if os.path.exists(audio_dir):
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
    # Turn off reloader to avoid multiprocessing issues and optimize startup
    app.run(host="127.0.0.1", port=2000, debug=False, use_reloader=False)

if __name__ == "__main__":
    run_server()
