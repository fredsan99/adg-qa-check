import os
import shutil
import datetime
from pathlib import Path

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
ROOT = r"C:\Users\frede\Desktop\projects\ADG QA Script\test_dirs"

# Offices to create
OFFICES = ["SSC", "GLC", "SYD"]

# Disciplines to create in each project
DISCIPLINES = ["CVL", "STR", "ARC"]

# Which sample structure(s) to create per office
# - old:  OFFICE\25000\25633\DISCIPLINE\RCRD CPY\...
# - new:  OFFICE\27000\27170\27170.001\DISCIPLINE\RCRD CPY\...
CREATE_OLD_STRUCTURE = True
CREATE_NEW_STRUCTURE = True

# Whether to wipe ROOT before generating (safe-guarded)
WIPE_EXISTING = True

# File scenarios: (relative subpath under RCRD CPY, file name, days_ago)
# Adjust days_ago to simulate recency vs. stale files
FILE_SCENARIOS = [
    ("",                 "readme.txt",              1),   # recent in root of RCRD CPY
    ("issued",           "package_list.txt",        3),   # recent in subfolder
    ("issued\\drawings",  "sheet_register.txt",      10),  # older than a 4-day threshold
    ("WIP",              "notes.txt",               0),   # modified today
    ("archive",          "old_issue_log.txt",       30),  # old
]

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def safe_wipe(root: str):
    """
    Deletes the given root directory if it exists and looks like our test root.
    Guard prevents accidental deletion elsewhere.
    """
    root_path = Path(root)
    if not root_path.exists():
        return
    # Basic guard: require 'test_dirs' as the tail of the path
    if root_path.name.lower() != "test_dirs":
        raise RuntimeError(f"Refusing to delete non-test path: {root}")
    shutil.rmtree(root)

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def create_file_with_mtime(path: Path, days_ago: int, contents: str = ""):
    ensure_dir(path.parent)
    path.write_text(contents or f"Test file: {path.name}\nSimulated age: {days_ago} day(s) ago.\n", encoding="utf-8")
    # Set modified time to 'days_ago'
    target_dt = datetime.datetime.now() - datetime.timedelta(days=days_ago)
    ts = target_dt.timestamp()
    os.utime(path, (ts, ts))

def create_project_old(office_path: Path, group: str, project: str):
    """
    Old layout:
    ROOT\\OFFICE\\{group}\\{project}\\{discipline}\\RCRD CPY\\...
    """
    group_path = office_path / group
    for disc in DISCIPLINES:
        rcrd = group_path / project / disc / "RCRD CPY"
        for subdir, fname, days_ago in FILE_SCENARIOS:
            fpath = rcrd / subdir / fname
            create_file_with_mtime(fpath, days_ago, contents=f"{office_path.name}-{group}-{project}-{disc}")

def create_project_new(office_path: Path, group: str, project: str, sub_suffix: str = "001"):
    """
    New layout:
    ROOT\\OFFICE\\{group}\\{project}\\{project}.{sub_suffix}\\{discipline}\\RCRD CPY\\...
    """
    subproj = f"{project}.{sub_suffix}"
    for disc in DISCIPLINES:
        rcrd = office_path / group / project / subproj / disc / "RCRD CPY"
        for subdir, fname, days_ago in FILE_SCENARIOS:
            fpath = rcrd / subdir / fname
            create_file_with_mtime(fpath, days_ago, contents=f"{office_path.name}-{group}-{project}-{subproj}-{disc}")

# -----------------------------------------------------------------------------
# MAIN GENERATOR
# -----------------------------------------------------------------------------
def main():
    # Optional wipe
    if WIPE_EXISTING:
        safe_wipe(ROOT)

    root_path = Path(ROOT)
    ensure_dir(root_path)

    for office in OFFICES:
        office_path = root_path / office
        ensure_dir(office_path)

        # Use fixed IDs so you get predictable paths your scanner will find
        if CREATE_OLD_STRUCTURE:
            # Example old: group 25000 with projects 25633 and 25640
            create_project_old(office_path, group="25000", project="25633")
            create_project_old(office_path, group="25000", project="25640")
            create_project_old(office_path, group="27000", project="27868")

        if CREATE_NEW_STRUCTURE:
            # Example new: group 27000 with project 27170 (sub 27170.001)
            create_project_new(office_path, group="27000", project="27170", sub_suffix="001")
            # Another new with a different sub-suffix for variety
            create_project_new(office_path, group="27000", project="27180", sub_suffix="005")
            create_project_new(office_path, group="24000", project="24324", sub_suffix="002")
            create_project_new(office_path, group="24000", project="24324", sub_suffix="003")

    print(f"Test directory tree created under:\n{ROOT}")

if __name__ == "__main__":
    main()
