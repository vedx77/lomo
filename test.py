import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import win32evtlog

class LogViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Log Viewer")
        self.create_widgets()

    def create_widgets(self):
        # Set background color for the window
        self.root.configure(bg="#d3d3d3")

        # Add a central "Monitor Logs" button
        monitor_button = tk.Button(
            self.root,
            text="MONITOR LOGS",
            bg='#a9a9a9',
            fg='white',
            font=('Arial', 14, 'bold'),
            width=20,
            height=2,
            relief='raised',
            bd=3
        )
        monitor_button.pack(pady=20)

        # Add a welcome label
        welcome_label = tk.Label(
            self.root,
            text="WELCOME USER, YOU'RE USING WINDOWS MACHINE",
            bg='#d3d3d3',
            fg='black',
            font=('Arial', 14)
        )
        welcome_label.pack(pady=10)

        # Create a frame for the main buttons
        button_frame = tk.Frame(self.root, bg="#d3d3d3", pady=20)
        button_frame.pack(pady=20)

        # Add buttons for Windows logs
        log_types = ['APPLICATION', 'SECURITY', 'SETUP', 'SYSTEM', 'FOR. EVENTS']
        button_colors = ['#d4af37', '#00cfff', '#ff69b4', '#ffeb3b', '#9370db']

        self.buttons = {}
        for log_type, color in zip(log_types, button_colors):
            button = tk.Button(
                button_frame,
                text=log_type,
                bg=color,
                fg='black',
                font=('Arial', 12, 'bold'),
                width=12,
                height=2,
                relief='raised',
                bd=3,
                command=lambda lt=log_type: self.show_logs(lt),
                highlightbackground=color,
                highlightthickness=2
            )
            # Apply round edges
            button.config(relief='flat', bd=0, padx=10, pady=5)
            button.pack(side=tk.LEFT, padx=15, pady=10, ipadx=10, ipady=10)
            self.buttons[log_type] = button

        # Create a frame for displaying logs with scrollbars
        self.log_frame = tk.Frame(self.root, bg="#f9f9f9")
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Add vertical scrollbar to the log frame
        self.scrollbar_y = tk.Scrollbar(self.log_frame, orient=tk.VERTICAL)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Add horizontal scrollbar at the bottom
        self.scrollbar_x = tk.Scrollbar(self.root, orient=tk.HORIZONTAL)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Create a Treeview for displaying logs
        self.tree = ttk.Treeview(self.log_frame, columns=['Time', 'Event ID', 'Source', 'Event Type', 'Message'], show='headings',
                                 yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)
        self.tree.pack(expand=True, fill='both')

        # Configure scrollbars
        self.scrollbar_y.config(command=self.tree.yview)
        self.scrollbar_x.config(command=self.tree.xview)

        # Define the columns with wider widths for horizontal scrolling
        columns = ['Time', 'Event ID', 'Source', 'Event Type', 'Message']
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center', width=300)  # Increase width for better visibility and scrolling

        # Add the "Save Log" button at the bottom right
        save_button = tk.Button(
            self.root,
            text="SAVE LOG",
            bg='#4caf50',
            fg='white',
            font=('Arial', 12, 'bold'),
            width=10,
            height=2,
            relief='raised',
            bd=3,
            command=self.confirm_save_logs
        )
        save_button.pack(side=tk.BOTTOM, anchor=tk.SE, padx=20, pady=20)

    def fetch_logs(self, log_type):
        logs = []
        try:
            server = 'localhost'
            hand = win32evtlog.OpenEventLog(server, log_type)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            for event in events:
                logs.append([
                    event.TimeGenerated.Format(),
                    event.EventID,
                    event.SourceName,
                    event.EventType,
                    event.StringInserts
                ])
            win32evtlog.CloseEventLog(hand)
        except Exception as e:
            print(f"Error fetching {log_type} logs: {e}")
        return logs

    def display_logs(self, logs):
        # Clear the treeview before inserting new logs
        self.tree.delete(*self.tree.get_children())

        for log in logs:
            self.tree.insert("", "end", values=log)

    def show_logs(self, log_type):
        logs = self.fetch_logs(log_type)
        self.display_logs(logs)

    def confirm_save_logs(self):
        if messagebox.askyesno("Save Logs", "Do you want to save the logs?"):
            self.save_selected_logs()
        else:
            messagebox.showinfo("Info", "Logs not saved.")

    def save_selected_logs(self):
        selected_logs = []

        def ask_user_to_select_logs():
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Logs to Save")
            dialog.config(bg="#f9f9f9")

            tk.Label(dialog, text="Select logs to save:", bg="#f9f9f9", font=('Arial', 12)).pack(anchor=tk.W, padx=10, pady=5)

            log_vars = {}

            for log_type in self.buttons.keys():
                var = tk.BooleanVar(value=False)
                log_vars[log_type] = var
                tk.Checkbutton(dialog, text=log_type, variable=var, bg="#f9f9f9", font=('Arial', 12)).pack(anchor=tk.W, padx=10)

            def confirm_selection():
                nonlocal selected_logs
                selected_logs = [log for log, var in log_vars.items() if var.get()]
                dialog.destroy()

            tk.Button(dialog, text="Save", command=confirm_selection, bg="#4caf50", fg='white', font=('Arial', 12)).pack(pady=10)
            dialog.transient(self.root)
            dialog.grab_set()
            self.root.wait_window(dialog)

        ask_user_to_select_logs()

        if selected_logs:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("Log Files", "*.log")],
                initialfile="selected_logs.txt",
                title="Save Log File"
            )

            if filename:
                with open(filename, 'w') as f:
                    for log_type in selected_logs:
                        logs = self.fetch_logs(log_type)
                        if logs:
                            f.write(f"===== {log_type} Logs =====\n")
                            for log in logs:
                                f.write(f"Time: {log[0]}, Event ID: {log[1]}, Source: {log[2]}, Event Type: {log[3]}, Message: {log[4]}\n")
                            f.write("\n")
                    messagebox.showinfo("Success", f"Selected logs saved to {filename}")
        else:
            messagebox.showinfo("Info", "No log types selected.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LogViewerApp(root)
    root.mainloop()
