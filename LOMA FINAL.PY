import tkinter as tk
from tkinter import ttk  # Ensure this import is present
from tkinter import filedialog, messagebox, PhotoImage, BooleanVar
from tkinter.scrolledtext import ScrolledText
import threading
import json
import time
import platform
import os
from evtx import PyEvtxParser
try:
    import win32evtlog  # Windows-specific library
except ImportError:
    win32evtlog = None  # Handle gracefully for Linux systems

global_logs = []  # Store logs in memory
monitoring = False  # Control the state of live monitoring
log_display_count = 10  # Default number of logs to display

# Function to map the event level to severity categories
def map_event_level(level):
    severity_mapping = {
        1: "Critical",
        2: "Error",
        3: "Warning",
        4: "Information",
        5: "Audit Success",
        6: "Audit Failure"
    }
    return severity_mapping.get(level, "Unknown")

# Function to fetch logs live (for Windows)
def fetch_windows_live_logs():
    global monitoring
    server = 'localhost'
    logtype = 'System'

    while monitoring:
        try:
            handler = win32evtlog.OpenEventLog(server, logtype)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            events = win32evtlog.ReadEventLog(handler, flags, 0)
            
            for event in events:
                log = {
                    "EventID": event.EventID,
                    "Timestamp": event.TimeGenerated.Format(),
                    "Level": map_event_level(event.EventType),
                    "Provider": event.SourceName,
                    "Description": event.StringInserts[0] if event.StringInserts else "N/A"
                }
                global_logs.append(log)
                display_logs(global_logs[-log_display_count:])  # Display based on selected count
            time.sleep(2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch live logs: {e}")
            break

# Function to fetch logs live (for Linux)
def fetch_linux_live_logs():
    global monitoring
    log_file = "/var/log/syslog" if os.path.exists("/var/log/syslog") else "/var/log/messages"

    with open(log_file, "r") as f:
        f.seek(0, os.SEEK_END)  
        while monitoring:
            line = f.readline()
            if not line:
                time.sleep(1)
                continue

            log = {
                "EventID": "N/A",
                "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "Level": "Information",  
                "Provider": "System",
                "Description": line.strip()
            }
            global_logs.append(log)
            display_logs(global_logs[-log_display_count:])  # Display based on selected count

# Function to update the number of logs to display based on user selection
def update_display_count(event):
    global log_display_count
    log_display_count = int(dropdown_var.get())

# Function to start live monitoring
def start_live_monitoring():
    global monitoring
    if monitoring:
        messagebox.showwarning("Monitoring", "Live monitoring is already running.")
        return

    monitoring = True
    if platform.system() == "Windows" and win32evtlog:
        threading.Thread(target=fetch_windows_live_logs, daemon=True).start()
    elif platform.system() == "Linux":
        threading.Thread(target=fetch_linux_live_logs, daemon=True).start()
    else:
        messagebox.showerror("Unsupported OS", "Live monitoring is not supported on this OS.")

# Function to stop live monitoring
def stop_live_monitoring():
    global monitoring
    monitoring = False
    messagebox.showinfo("Stopped", "Live monitoring has been stopped.")



# Function to parse the .evtx file
def parse_event_log(file_path):
    logs = []
    parser = PyEvtxParser(file_path)
    try:
        for record in parser.records_json():
            event_data = json.loads(record['data']).get('Event', {})
            event_id_data = event_data.get('System', {}).get('EventID', {})
            if isinstance(event_id_data, dict):
                    # If it's a dictionary, get the text representation
                event_id = event_id_data.get('#text', 'N/A')
            else:
                    # If it's not a dictionary, use the integer value directly
                event_id = event_id_data
            # event_id = event_data.get('Event', {}).get('EventID', {}).get('#text', 'N/A')
            timestamp = record['timestamp']
            # print(event_data)
            level_value = event_data.get('System', {}).get('Level', 'N/A')
            level = map_event_level(level_value)

            provider = event_data.get('System', {}).get('Provider', {}).get('#attributes', {}).get('Name', 'N/A')
            
            # Assuming Description Data is stored in EventData
            description_data = event_data.get('EventData', {})
            if description_data is None:
                description_data = 'N/A'
            else:
                description_data = description_data.get('Data', {}).get('#text', 'N/A')
                if description_data is None:
                    description_data = 'N/A'
                else:
                    description_data = "\n".join(description_data)
            logs.append({
                "EventID": event_id,
                "Timestamp": timestamp,
                "Level": level,
                "Provider": provider,
                "Description": description_data
            })
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
    return logs

# Function to display logs with enhanced formatting
def display_logs(logs):
    output_area.delete(1.0, tk.END)  # Clear the output area
    for i, log in enumerate(logs, start=1):
        log_header = f"Log {i} - {log['Level']} Event (ID: {log['EventID']})\n"
        
        # Differentiate log levels for criticality
        if log['Level'] == "Critical":
            output_area.insert(tk.END, log_header, "critical")
        elif log['Level'] == "Error":
            output_area.insert(tk.END, log_header, "error")
        elif log['Level'] == "Information":
            output_area.insert(tk.END, log_header, "information")
        elif log['Level'] == "Audit Success":
            output_area.insert(tk.END, log_header, "audit_s")
        elif log['Level'] == "Audit Failure":
            output_area.insert(tk.END, log_header, "audit_f")
        elif log['Level'] == "Warning":
            output_area.insert(tk.END, log_header, "warning")
        else:
            output_area.insert(tk.END, log_header, "normal")
        
        # Show more details in an organized manner
        output_area.insert(tk.END, f"Timestamp: {log['Timestamp']}\n", "normal")
        output_area.insert(tk.END, f"Provider: {log['Provider']}\n", "normal")
        output_area.insert(tk.END, f"Description: {log['Description']}\n", "description")
        output_area.insert(tk.END, "-"*50 + "\n", "separator")

# Function to generate a report
def generate_report():
    if not global_logs:
        messagebox.showwarning("No Logs", "No logs available to generate a report.")
        return

    filters = apply_filters()  # Get the selected filters

    # Use threading to prevent blocking the UI
    report_thread = threading.Thread(target=generate_report_in_background, args=(filters,))
    report_thread.start()

def generate_report_in_background(filters):
    filtered_logs = [log for log in global_logs if log['Level'] in filters]
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".evtx", 
        filetypes=[("Event Files", "*.evtx"), ("CSV files", "*.csv")],
        title="Save Report"
    )
    
    if not file_path:
        return
    
    try:
        with open(file_path, 'w', encoding='utf-8', errors='replace') as file:
            file.write("Filtered EVTX Log Report\n")
            file.write("="*50 + "\n")
            for i, log in enumerate(filtered_logs, start=1):
                file.write(f"Log {i} - {log['Level']} Event (ID: {log['EventID']})\n")
                file.write(f"Timestamp: {log['Timestamp']}\n")
                file.write(f"Provider: {log['Provider']}\n")
                file.write(f"Description: {log['Description']}\n")
                file.write("-"*50 + "\n")
        
        messagebox.showinfo("Report Generated", f"Report saved successfully to: {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save the report: {str(e)}")

# Function to apply severity filters
def apply_filters():
    filters = []
    if critical_var.get():
        filters.append("Critical")
    if error_var.get():
        filters.append("Error")
    if warning_var.get():
        filters.append("Warning")
    if info_var.get():
        filters.append("Information")
    if audit_success_var.get():
        filters.append("Audit Success")
    if audit_failure_var.get():
        filters.append("Audit Failure")
    if unknown_var.get():
        filters.append("Unknown")
    
    filtered_logs = [log for log in global_logs if log['Level'] in filters]
    display_logs(filtered_logs)
    
    return filters  # Return selected filters for report generation

# Function to handle file loading in a separate thread
def load_file():
    file_path = filedialog.askopenfilename(filetypes=[("EVTX Files", "*.evtx")])
    if not file_path:
        file_label.config(text="No file selected.")
        return
    
    file_label.config(text=f"Loaded: {file_path}")
    load_thread = threading.Thread(target=parse_and_display_logs, args=(file_path,))
    load_thread.start()

def parse_and_display_logs(file_path):
    global global_logs
    global_logs = parse_event_log(file_path)
    display_logs(global_logs)

# Function to toggle the side panel
def toggle_side_panel():
    if side_panel.winfo_ismapped():
        side_panel.pack_forget()
        toggle_button.config(text="Show Filters")
    else:
        side_panel.pack(side=tk.RIGHT, fill=tk.Y)  # Ensure the side panel is packed on the right side
        toggle_button.config(text="Hide Filters")

def show_message():
    messagebox.showinfo("Message", "Hello, this is a message!")

# Main application window
root = tk.Tk()
root.title("LOMA")
root.geometry("1200x800")

color1 = '#020f12' #Black
color2 = '#000f25' #Dark Blue
color3 = '#b3cde0' #Button Unclicked
color4 = 'white' #
color5 = '#000916' #
color6 = '#6497b1' #Button Clicked

# Top frame for file label and buttons
top_frame = tk.Frame(root, bg=color5)
top_frame.pack(side=tk.TOP, fill=tk.X)

# Dropdown 1 - for selecting the number of logs to display
dropdown_var = tk.StringVar(value="10")
dropdown = ttk.Combobox(top_frame, textvariable=dropdown_var, state="readonly", font=('Arial', 12), width=4)
dropdown['values'] = [10, 50, 100, 250, 500, 1000]
dropdown.bind("<<ComboboxSelected>>", update_display_count)
dropdown.pack(side=tk.RIGHT, padx=10, pady=10)

# Label 1 - Max log count selection label
count_label = tk.Label(top_frame, text="Select maximum no. of logs to be displayed:", bg=color5, foreground='white', anchor="w")
count_label.pack(side=tk.RIGHT, padx=0, pady=10)

# Button 1 - Stop Live Monitoring
stop_button = tk.Button(top_frame, bg='#6b7b86', foreground='white', font=('Arial', 12, 'bold'),
                        activebackground=color6, activeforeground=color4,
                        width=10, wraplength=90, height=2,
                        text="Stop Live Monitoring", command=stop_live_monitoring)
stop_button.pack(side=tk.RIGHT, padx=10, pady=10)

# Button 2 - Start Live Monitoring
load_button = tk.Button(top_frame, bg='#6b7b86', foreground='white', font=('Arial', 12, 'bold'),
                        activebackground=color6, activeforeground=color4,
                        width=10, wraplength=90, height=2,
                        text="Start Live Monitoring", command=start_live_monitoring)
load_button.pack(side=tk.RIGHT, padx=10, pady=10)

output_area = ScrolledText(root, wrap=tk.WORD, bg=color2, fg='white')

for tag, color in [("critical", "red"),
                   ("error", "orange"),
                   ("warning", "yellow"),
                   ("information", "blue"),
                   ("description", "white"),
                   ("separator", "gray")]:
    output_area.tag_config(tag, foreground=color, font=("Arial", 12, "bold"))


# Label 2 - File selection label
file_label = tk.Label(top_frame, text="No file selected.", bg=color5, foreground='white', anchor="w")
file_label.pack(side=tk.LEFT, padx=10, pady=10)

# Button 3 - Load & Parse Logs
load_button = tk.Button(top_frame, bg=color3,  font=('Arial', 12, 'bold'),
                        activebackground=color6, activeforeground=color4,
                        width=10, wraplength=90, height=2,
                        text="Load & Parse Logs", command=load_file)
load_button.pack(side=tk.RIGHT, padx=10, pady=10)

# Button 4 - Toggle side panel
toggle_button = tk.Button(top_frame, bg=color3, font=('Arial', 12, 'bold'), 
                          activebackground=color6, activeforeground=color4,
                          width=10, wraplength=75, height=2,
                          text="Hide Filters", command=toggle_side_panel)
toggle_button.pack(side=tk.RIGHT, padx=10, pady=15)

def create_checkbutton_images():
    # Create images for the checked and unchecked states
    unchecked_image = PhotoImage(width=20, height=20)
    unchecked_image.put(("gray", "gray"), to=(0, 0, 20, 20))  # Placeholder for unchecked
    
    checked_image = PhotoImage(width=20, height=20)
    checked_image.put(("blue", "blue"), to=(0, 0, 20, 20))  # Placeholder for checked

    return unchecked_image, checked_image

# Main content frame
content_frame = tk.Frame(root, bg=color1)
content_frame.pack(fill=tk.BOTH, expand=True)

# Scrollable text area for logs
output_area = ScrolledText(content_frame, wrap=tk.WORD, bg=color2, foreground='white')
output_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Apply styles for critical logs
output_area.tag_config("critical", foreground="red", font=("Arial", 12, "bold"))
output_area.tag_config("error", foreground="orange", font=("Arial", 12, "bold"))
output_area.tag_config("warning", foreground="yellow", font=("Arial", 12, "bold"))
output_area.tag_config("information", foreground="blue", font=("Arial", 12, "bold"))
output_area.tag_config("audit_s", foreground="green", font=("Arial", 12, "bold"))
output_area.tag_config("audit_f", foreground="maroon", font=("Arial", 12, "bold"))
output_area.tag_config("description", foreground="white", font=("Arial", 10, "italic"))
output_area.tag_config("separator", foreground="gray")

# Side panel with filter options
side_panel = tk.Frame(content_frame, relief=tk.RAISED, bd=2, bg=color5)
side_panel.pack(side=tk.RIGHT, fill=tk.Y)

# Filter checkboxes label
filter_label = tk.Label(side_panel, text="Filter Logs by Severity", bg='#020f12', foreground='white', font=('Arial', 16, 'bold'))
filter_label.pack(pady=10, padx=10)

# Create custom checkbutton images
unchecked_image, checked_image = create_checkbutton_images()

# Boolean variables for checkboxes
critical_var = BooleanVar(value=True)
error_var = BooleanVar(value=True)
warning_var = BooleanVar(value=True)
info_var = BooleanVar(value=True)
audit_success_var = BooleanVar(value=True)
audit_failure_var = BooleanVar(value=True)
unknown_var = BooleanVar(value=True)

# Create the checkbuttons
tk.Checkbutton(side_panel, text="Critical", bg='#020f12', fg='white', activebackground='#020f12',
               variable=critical_var, selectcolor='#6497b1', 
               compound=tk.LEFT).pack(anchor='w', padx=10)
tk.Checkbutton(side_panel, text="Error", bg='#020f12', fg='white', variable=error_var,
               selectcolor='#6497b1', compound=tk.LEFT).pack(anchor='w', padx=10)
tk.Checkbutton(side_panel, text="Warning", bg='#020f12', fg='white', variable=warning_var,
               selectcolor='#6497b1', compound=tk.LEFT).pack(anchor='w', padx=10)
tk.Checkbutton(side_panel, text="Information", bg='#020f12', fg='white', variable=info_var,
               selectcolor='#6497b1', compound=tk.LEFT).pack(anchor='w', padx=10)
tk.Checkbutton(side_panel, text="Audit Success", bg='#020f12', fg='white', variable=audit_success_var,
               selectcolor='#6497b1', compound=tk.LEFT).pack(anchor='w', padx=10)
tk.Checkbutton(side_panel, text="Audit Failure", bg='#020f12', fg='white', variable=audit_failure_var,
               selectcolor='#6497b1', compound=tk.LEFT).pack(anchor='w', padx=10)
tk.Checkbutton(side_panel, text="Unknown", bg='#020f12', fg='white', variable=unknown_var,
               selectcolor='#6497b1', compound=tk.LEFT).pack(anchor='w', padx=10)

# Generate Report button
generate_report_button = tk.Button(side_panel, bg=color3, font=('Arial', 12, 'bold'),
                                   activebackground=color2, activeforeground=color1,
                                   width=15, wraplength=90, height=2,
                                   text="Generate Report", command=generate_report)
generate_report_button.pack(side=tk.BOTTOM, pady=15)

# Apply Filters button
apply_filters_button = tk.Button(side_panel, bg=color3, font=('Arial', 12, 'bold'),
                                 activebackground=color2, activeforeground=color1,
                                 width=15, wraplength=60, height=2,
                                 text="Apply Filters", command=apply_filters)
apply_filters_button.pack(side=tk.BOTTOM)

# Start the main application loop
root.mainloop()