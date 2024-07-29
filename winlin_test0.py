import platform
import sys
import tkinter as tk
from tkinter import messagebox

def get_os_info():
    os_name = platform.system()
    os_version = platform.version()
    os_release = platform.release()

    if os_name == "Windows":
        # Use sys.getwindowsversion() for better Windows version details
        win_ver = sys.getwindowsversion()
        major, minor, build = win_ver.major, win_ver.minor, win_ver.build
        
        # Determine specific Windows versions
        if major == 10 and minor == 0:
            if build >= 22000:
                os_version = "Windows 11"
            else:
                os_version = "Windows 10"
        elif major == 6:
            if minor == 1:
                os_version = "Windows 7"
            elif minor == 2:
                os_version = "Windows 8"
            elif minor == 3:
                os_version = "Windows 8.1"
        elif major == 5 and minor == 1:
            os_version = "Windows XP"
        else:
            os_version = f"Windows {os_release} (Build {build})"

    elif os_name == "Linux":
        distro_name, distro_version, _ = platform.linux_distribution(full_distribution_name=False)
        os_version = f"{distro_name.capitalize()} {distro_version}"
    elif os_name == "Darwin":
        os_version = "macOS " + platform.mac_ver()[0]
    else:
        os_version = f"{os_name} {os_version}"

    return os_version

def show_os_info():
    os_info = get_os_info()
    messagebox.showinfo("Operating System Info", f"Detected OS: {os_info}")

# Create a simple GUI
root = tk.Tk()
root.title("OS Detector")
root.geometry("300x200")

label = tk.Label(root, text="Click the button to detect your OS", font=("Arial", 12))
label.pack(pady=20)

button = tk.Button(root, text="Detect OS", command=show_os_info, font=("Arial", 12))
button.pack(pady=20)

root.mainloop()
