import os
import sys
import subprocess

def create_shortcuts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pythonw_exe = sys.executable
    if "python.exe" in pythonw_exe.lower():
        pythonw_candidate = pythonw_exe.lower().replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw_candidate):
            pythonw_exe = pythonw_candidate

    target_script = os.path.join(base_dir, "launch_app.pyw")
    icon_path = os.path.join(base_dir, "app_icon.ico")
    
    desktop_dirs = [
        os.path.expanduser(r"~\Desktop"),
        os.path.expanduser(r"~\OneDrive\Desktop")
    ]

    created = []

    for desktop in desktop_dirs:
        if os.path.exists(desktop):
            shortcut_path = os.path.join(desktop, "ShortCraft AI.lnk")
            
            # PowerShell command using WScript.Shell
            ps_cmd = f"""
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{pythonw_exe}"
            $Shortcut.Arguments = '"{target_script}"'
            $Shortcut.WorkingDirectory = "{base_dir}"
            $Shortcut.IconLocation = "{icon_path},0"
            $Shortcut.Description = "ShortCraft AI - YouTube to Shorts Generator"
            $Shortcut.Save()
            """
            
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
            if res.returncode == 0 and os.path.exists(shortcut_path):
                created.append(shortcut_path)

    return created

if __name__ == "__main__":
    shortcuts = create_shortcuts()
    print("Created shortcuts:", shortcuts)
