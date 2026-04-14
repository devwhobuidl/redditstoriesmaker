import webview
import threading
import time
import sys
import os
from app import demo, REDDIT_THEME_CSS

def start_gradio():
    # Launch without blocking and without opening browser tab
    demo.launch(
        server_name="127.0.0.1",
        server_port=7865, 
        prevent_thread_lock=True,
        show_error=True,
        quiet=True
    )

def main():
    # Start Gradio in a daemon thread
    t = threading.Thread(target=start_gradio)
    t.daemon = True
    t.start()

    # Wait a moment for server to warm up
    time.sleep(2)

    # Create native window
    window = webview.create_window(
        'RedditStoryVideoMaker Desktop', 
        'http://127.0.0.1:7865',
        width=1280,
        height=900,
        min_size=(1024, 800),
        confirm_close=True
    )
    
    # Start the webview loop
    webview.start(debug=False)

if __name__ == "__main__":
    main()
