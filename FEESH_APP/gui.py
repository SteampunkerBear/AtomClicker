import subprocess
import webview
import os

# Change to the directory where manage.py lives
os.chdir("..")  # Adjust this if your structure is different

# Start Django server
subprocess.Popen(["python", "manage.py", "runserver"])

# Launch PyWebView
webview.create_window("FEESH Game", "http://127.0.0.1:8000/")
webview.start()