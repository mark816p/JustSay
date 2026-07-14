import webview
import sys
import time
import requests

def run_webview_app():
    url = "http://localhost:2000"
    
    # Wait for the server to be up before showing the window
    max_retries = 20
    for i in range(max_retries):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)

    # Launch native window wrapping the local server
    window = webview.create_window(
        'JustSay Dashboard', 
        url, 
        width=1024, 
        height=768, 
        resizable=True,
        min_size=(800, 600)
    )
    webview.start(private_mode=False)

if __name__ == '__main__':
    run_webview_app()
