import os
import datetime


# Script not checked yet, just copilot
# Purpose: This script will take a directory as well as a list of strings
# and search for filenames in the directory and all subdirectories
# that satisfy all of the following conditions: 
# At least one of the strings in the list is part of the filename
# The file was modified within the last week.
# The file type is a pdf file.
# The script will then return a dictionary with the filenames as keys and the modified date as values.

def main():
    # clear command line
    os.system('cls' if os.name == 'nt' else 'clear')

    base_dirs = [r"C:\Users\frede\Desktop\QUT"]
    days_threshold = 7
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_threshold)

    matching_files = {}
    def scan_directory(base_dir):
        try:
            with os.scandir(base_dir) as entries:
                for entry in entries:
                    if entry.is_dir():
                        scan_directory(entry.path)  # Recurse into subdirectories
                    elif entry.is_file():
                        if entry.name.endswith('.pdf'):
                            file_mod_time = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
                            if file_mod_time >= cutoff_date:
                                matching_files[entry.name] = file_mod_time
        except Exception as e:
            print(f"Skipping {base_dir}: {e}")

    # Run scan
    for base_dir in base_dirs:
        scan_directory(base_dir)

    print("Matching Files:", matching_files)