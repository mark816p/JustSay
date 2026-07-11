from flask import Flask, render_template_string, request, redirect, url_for, send_file
import database
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>JustSay - Local Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #121212; color: #ffffff; margin: 0; padding: 20px; }
        h1 { color: #bb86fc; }
        .section { background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #333; padding: 10px; text-align: left; }
        th { background-color: #2c2c2c; }
        input[type="text"] { width: 80%; padding: 8px; background-color: #333; color: white; border: 1px solid #444; border-radius: 5px; }
        button { background-color: #bb86fc; color: #000; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background-color: #9965f4; }
        .audio-player { width: 250px; height: 30px; }
    </style>
</head>
<body>
    <h1>JustSay Dashboard</h1>
    
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
                <td>{% if p.is_active %}⭐ Active{% else %}<a href="/set_active/{{ p.id }}" style="color: #bb86fc;">Set Active</a>{% endif %}</td>
                <td>{{ p.prompt_text }}</td>
                <td><a href="/delete_prompt/{{ p.id }}" style="color: #cf6679;">Delete</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="section">
        <h2>Dictation History</h2>
        <table>
            <tr>
                <th>Date / Time</th>
                <th>Transcript</th>
                <th>Audio</th>
            </tr>
            {% for h in history %}
            <tr>
                <td>{{ h.timestamp }}</td>
                <td>{{ h.transcript }}</td>
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

@app.route("/")
def index():
    prompts = database.get_all_prompts()
    history = database.get_history()
    return render_template_string(HTML_TEMPLATE, prompts=prompts, history=history)

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
    # Security note: in a real app, ensure filename prevents directory traversal
    audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "history_audio"))
    return send_file(os.path.join(audio_dir, filename))

def run_server():
    database.init_db()
    # Ensure audio dir exists
    audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "history_audio"))
    os.makedirs(audio_dir, exist_ok=True)
    # Run on 2000
    app.run(host="127.0.0.1", port=2000, debug=False, use_reloader=False)

if __name__ == "__main__":
    run_server()
