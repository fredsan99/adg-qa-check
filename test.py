import os
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd

# Predefined office locations and disciplines
OFFICES = ["SSC", "ABC", "XYZ"]  # Modify as needed
DISCIPLINES = ["CVL", "STR", "ELE"]  # Modify as needed

def run_script():
    """Fetches user-selected inputs and runs the main script."""
    selected_offices = [office for office, var in office_vars.items() if var.get()]
    selected_disciplines = [discipline for discipline, var in discipline_vars.items() if var.get()]
    days_threshold = int(days_threshold_entry.get()) if days_threshold_entry.get().isdigit() else 21

    if not selected_offices or not selected_disciplines:
        messagebox.showerror("Input Error", "Please select at least one office and one discipline.")
        return

    messagebox.showinfo("Processing", "Scanning directories. This may take some time...")

    # Run the main script with user-selected inputs
    base_dirs = [f"\\\\adgce.local\\projects\\{office}" for office in selected_offices]

    def get_project_group_dirs():
        """Returns project group directories (5-digit numbers)."""
        project_group_dirs = []
        for base_dir in base_dirs:
            with os.scandir(base_dir) as entries:
                for entry in entries:
                    if entry.is_dir() and entry.name.isdigit() and len(entry.name) == 5:
                        project_group_dirs.append(entry.path)
        return project_group_dirs

    base_dirs = get_project_group_dirs()

    def get_project_dirs():
        """Returns project directories inside project groups."""
        project_dirs = []
        for base_dir in base_dirs:
            with os.scandir(base_dir) as entries:
                for entry in entries:
                    if entry.is_dir():
                        project_dirs.append(entry.path)
        return project_dirs

    def get_rcrd_cpy_dirs(project_dirs):
        """Returns RCRD CPY directories matching user-selected disciplines."""
        rcrd_cpy_dirs = []
        for project_dir in project_dirs:
            for discipline in selected_disciplines:
                discipline_dir = os.path.join(project_dir, discipline)
                if os.path.exists(os.path.join(discipline_dir, "RCRD CPY")):
                    rcrd_cpy_dirs.append(os.path.join(discipline_dir, "RCRD CPY"))
        return rcrd_cpy_dirs

    project_dirs = get_project_dirs()
    rcrd_cpy_dirs = get_rcrd_cpy_dirs(project_dirs)

    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_threshold)
    matching_dirs = set()

    def scan_directory(rcrd_cpy_dir):
        """Scans directories for recently modified files."""
        try:
            with os.scandir(rcrd_cpy_dir) as entries:
                for entry in entries:
                    if entry.is_dir():
                        scan_directory(entry.path)
                    elif entry.is_file():
                        if datetime.datetime.fromtimestamp(entry.stat().st_mtime) >= cutoff_date:
                            matching_dirs.add(os.path.dirname(entry.path))
                            return
        except Exception as e:
            print(f"Skipping {rcrd_cpy_dir}: {e}")

    for rcrd_cpy_dir in rcrd_cpy_dirs:
        scan_directory(rcrd_cpy_dir)

    if not matching_dirs:
        messagebox.showinfo("Scan Complete", "No recently modified directories found.")
        return

    # Save results to Excel
    df = pd.DataFrame({"Matching Directories": list(matching_dirs)})
    df.to_excel("matching_dirs.xlsx", index=False, engine="openpyxl")

    messagebox.showinfo("Scan Complete", "Results saved to matching_dirs.xlsx!")

# Create the GUI window
root = tk.Tk()
root.title("Directory Scanner")
root.geometry("400x400")

# Office selection
tk.Label(root, text="Select Office Locations:").pack()
office_vars = {office: tk.BooleanVar() for office in OFFICES}
for office, var in office_vars.items():
    tk.Checkbutton(root, text=office, variable=var).pack()

# Discipline selection
tk.Label(root, text="Select Disciplines:").pack()
discipline_vars = {discipline: tk.BooleanVar() for discipline in DISCIPLINES}
for discipline, var in discipline_vars.items():
    tk.Checkbutton(root, text=discipline, variable=var).pack()

# Days threshold input
tk.Label(root, text="Days Threshold:").pack()
days_threshold_entry = tk.Entry(root)
days_threshold_entry.insert(0, "21")  # Default value
days_threshold_entry.pack()

# Run button
run_button = tk.Button(root, text="Start Scan", command=run_script)
run_button.pack(pady=10)

root.mainloop()
