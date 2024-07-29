import win32evtlog
import datetime

# Define constants for event log types
EVENT_LOG_TYPES = {
    "Application": "Application",
    "System": "System",
    "Security": "Security",
    "Setup": "Setup",
    "ForwardedEvents": "ForwardedEvents",
}

def fetch_event_logs(log_type):
    try:
        # Open event log
        log_handle = win32evtlog.OpenEventLog(None, log_type)

        # Get total number of records
        total_records = win32evtlog.GetNumberOfEventLogRecords(log_handle)
        print(f"Total records in {log_type} log: {total_records}")

        # Read event logs
        events = win32evtlog.ReadEventLog(log_handle, win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ, 0)

        for event in events:
            event_id = event.EventID
            event_time = event.TimeGenerated.Format()
            event_source = event.SourceName
            event_category = event.EventCategory
            event_description = event.StringInserts

            print(f"Event ID: {event_id}, Time: {event_time}, Source: {event_source}")
            print(f"Category: {event_category}, Description: {event_description}")
            print("")

        # Close event log
        win32evtlog.CloseEventLog(log_handle)

    except Exception as e:
        print(f"Failed to fetch logs for {log_type}: {str(e)}")

if __name__ == "__main__":
    for log_type in EVENT_LOG_TYPES.values():
        print(f"Fetching logs for: {log_type}")
        fetch_event_logs(log_type)

