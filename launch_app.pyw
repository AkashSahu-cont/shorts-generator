import os
import sys
import time
import subprocess
import urllib.request
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:5000"

def is_server_running():
    try:
        with urllib.request.urlopen(URL, timeout=1) as res:
            return res.status == 200
    except Exception:
        return False

def main():
    # 1. Start Flask backend if not already active
    if not is_server_running():
        python_exe = sys.executable
        if "pythonw.exe" in python_exe.lower():
            python_exe = python_exe.lower().replace("pythonw.exe", "python.exe")
        
        app_py = os.path.join(BASE_DIR, "app.py")
        
        # Windows flag to start completely hidden without any black console window
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            [python_exe, app_py],
            cwd=BASE_DIR,
            creationflags=CREATE_NO_WINDOW
        )
        
        # Wait until server is responsive
        for _ in range(15):
            time.sleep(0.4)
            if is_server_running():
                break

    # 2. Launch in native-like standalone App window using Chrome or Edge
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    app_arg = f"--app={URL}"
    window_arg = "--window-size=1260,920"

    if os.path.exists(chrome_path):
        subprocess.Popen([chrome_path, app_arg, window_arg])
    elif os.path.exists(edge_path):
        subprocess.Popen([edge_path, app_arg, window_arg])
    else:
        webbrowser.open(URL)

if __name__ == "__main__":
    main()
