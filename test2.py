import win32evtlog
import tkinter as tk
from tkinter import ttk, scrolledtext

# Refined fetch_logs function
def fetch_logs():
    log_type = "System"
    server = "localhost"
    hand = win32evtlog.OpenEventLog(server, log_type)
    
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    events = win32evtlog.ReadEventLog(hand, flags, 0)

    for event in events:
        event_id = event.EventID
        source = event.SourceName
        message = ' '.join(event.StringInserts) if event.StringInserts else "No message"
        time_generated = event.TimeGenerated.Format()
        data = f"Event ID: {event_id}\nSource: {source}\nTime: {time_generated}\nMessage: {message}\n{'-'*80}\n"
        log_text.insert(tk.END, data)
    
    win32evtlog.CloseEventLog(hand)

# GUI setup
root = tk.Tk()
root.title("Windows Log Analyzer")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Log display area
log_text = scrolledtext.ScrolledText(mainframe, wrap=tk.WORD, width=100, height=30)
log_text.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Fetch button
fetch_button = ttk.Button(mainframe, text="Fetch Logs", command=fetch_logs)
fetch_button.grid(column=0, row=1, sticky=tk.W)

root.mainloop()