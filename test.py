import os
import datetime
import pandas as pd
import json
import tkinter as tk
from tkinter import messagebox

# Predefined office locations and disciplines
OFFICES = ["SSC", "GLC", "SYD", "DWN", "BNE", "MEL"]  # Modify as needed
DISCIPLINES = ["CVL", "STR", "ELEC", "HYD", "GEO", "CSS"]  # Modify as needed
DEFAULT_DAYS = 28

def run_script():
    """Fetches user-selected inputs and runs the main script."""
    selected_offices = [office for office, var in office_vars.items() if var.get()]
    selected_disciplines = [discipline for discipline, var in discipline_vars.items() if var.get()]

    if not selected_offices or not selected_disciplines:
        messagebox.showerror("Input Error", "Please select at least one office and one discipline.")
        return

    if days_threshold_entry.get().isdigit():
        days_threshold = int(days_threshold_entry.get())
    else:
        messagebox.showerror("Input Error", "Please enter a valid number of days.")
        return
    
    messagebox.showinfo("Processing", "Scanning directories. This may take some time...")

    base_dir = r"\\adgce.local\projects"
    master_dict = {office: {discipline: [] for discipline in selected_disciplines} for office in selected_offices}

    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_threshold)

    def get_office_dirs():
        """Returns a dictionary of selected office directories."""
        return {office: os.path.join(base_dir, office) for office in selected_offices}

    def get_project_group_dirs(office_dir):
        """Returns a list of project group directories inside an office directory."""
        return [entry.path for entry in os.scandir(office_dir) if entry.is_dir() and entry.name.isdigit() and len(entry.name) == 5]

    def get_project_dirs(project_group_dir):
        """Returns a list of project directories inside a project group directory."""
        return [entry.path for entry in os.scandir(project_group_dir) if entry.is_dir()]

    def get_rcrd_cpy_dirs(discipline, project_dir):
        """Returns the RCRD CPY directory for a given discipline and project directory."""
        rcrd_cpy_dir = os.path.join(project_dir, discipline, "RCRD CPY")
        return rcrd_cpy_dir if os.path.exists(rcrd_cpy_dir) else None

    def scan_directory(rcrd_cpy_dir):
        """Scans a RCRD CPY directory for recently modified files."""
        modified_dirs = []
        try:
            with os.scandir(rcrd_cpy_dir) as entries:
                for entry in entries:
                    if entry.is_file():
                        if datetime.datetime.fromtimestamp(entry.stat().st_mtime) >= cutoff_date:
                            modified_dirs.append(os.path.dirname(entry.path))
                            return modified_dirs
                    elif entry.is_dir():
                        tmp_modified_dirs = scan_directory(entry.path)
                        if tmp_modified_dirs:
                            modified_dirs.extend(tmp_modified_dirs)
            return modified_dirs
        except Exception as e:
            print(f"Skipping {rcrd_cpy_dir}: {e}")
            return []

    def master_dict_to_dataframe(master_dict):
        """Converts master_dict to a structured pandas DataFrame."""
        data = [[office, discipline, path] for office, disciplines in master_dict.items() for discipline, paths in disciplines.items() for path in paths]
        return pd.DataFrame(data, columns=["Office", "Discipline", "Path"])

    office_dirs = get_office_dirs()

    for office, office_dir in office_dirs.items():
        project_group_dirs = get_project_group_dirs(office_dir)
        for project_group_dir in project_group_dirs:
            project_dirs = get_project_dirs(project_group_dir)
            for project_dir in project_dirs:
                for discipline in selected_disciplines:
                    rcrd_cpy_dir = get_rcrd_cpy_dirs(discipline, project_dir)
                    if rcrd_cpy_dir:
                        mod_dirs = scan_directory(rcrd_cpy_dir)
                    else:
                        mod_dirs = []
                    master_dict[office][discipline].extend(mod_dirs)

    with open("recently_issued_folders.json", "w") as f:
        json.dump(master_dict, f, indent=4)

    df = master_dict_to_dataframe(master_dict)
    df.to_csv("recently_issued_folders.csv", index=False)

    messagebox.showinfo("Scan Complete", "Results saved to recently_issued_folders.csv!")

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
days_threshold_entry.insert(0, str(DEFAULT_DAYS))
days_threshold_entry.pack()

# Run button
run_button = tk.Button(root, text="Start Scan", command=run_script)
run_button.pack(pady=10)

root.mainloop()
