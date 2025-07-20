import os
import datetime
import pandas as pd
import json, csv
import logging

# The purpose of this script is to show which disciplines on which projects have modified files
# in their RCRD CPY directories within the last X days.
# Define the base directories to scan: All projects located in \\adgce.local\projects.
# Each office has a folder in the projects directory, as a three letter abbreviation of the location, eg. SSC
# Each project group has a folder in an office directory, as a five digit number, eg. 21000
# Each project has a folder in a project group directory, as a five digit number, eg. 21076.
# Each discipline has a folder in a project directory, eg. CVL or STR.
# Each discipline folder has a folder called RCRD CPY, which contains files and further subdirectories of interest.
# Example path: \\adgce.local\projects\SSC\25000\25633\CVL\RCRD CPY\files and further subdirectories.

# This script will scan the RCRD CPY directories for all projects at specified offices and disciplines
# Which offices and disciplines to scan is specified in lists defined at the top of the script.
# The script will look for files in the RCRD CPY directories that have been modified within the last 30 days.
# The end result will be a nested dictionary of the form:
# {Office: {Discipline: [Matching Directories]}}


# Configure logging for debugging purposes
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

base_dir = r"\\adgce.local\projects"
offices = ["SSC"]
disciplines = ["CVL"]
days_threshold = 21 # Set this variable to current the day of the month. The script will check for files modified ON or AFTER the cutoff date. 

def get_office_dirs(base_dir: str, offices: list) -> dict:
    # The input to this function is a base directory and a list of office short names (SSC, GLC, etc.).
    # This function will return a dictionary of directories for office folders in the base directory. 
    # The dict will be of the form {"SSC": \\adgce.local\projects\SSC}
    office_dirs = {office: os.path.join(base_dir, office) for office in offices}
    return office_dirs


def get_subdirectories(directory: str, filter_digits: int):
    # The input to this function is a directory path and an optional filter for the number of digits.
    # This function will return a list of valid subdirectories inside the given directory.
    # If filter_digits is provided, only directories with the specified digit length are returned.
    """Returns a list of valid subdirectories inside the given directory.

    Args:
        directory (str): The parent directory to scan.
        filter_digits (int, optional): If provided, only directories with the specified digit length are returned.
    
    Returns:
        list: A list of subdirectory paths.
    """
    try:
        return [
            entry.path for entry in os.scandir(directory)
            if entry.is_dir() and (filter_digits is None or (entry.name.isdigit() and len(entry.name) == filter_digits))
        ]
    except PermissionError:
        logging.warning(f"Permission denied: {directory}, skipping.")
    except Exception as e:
        logging.warning(f"Skipping {directory}: {e}")
        return []


def get_rcrd_cpy_dirs(discipline: str, project_dir: str):
    """Returns the RCRD CPY directory path if it exists."""
    # The input to this function is a single discipline and a single project directory
    # This function will return the directory for the RCRD CPY folder in the project directory.
    # The directory will be of the form \\adgce.local\projects\SSC\25000\25633\CVL\RCRD CPY
    # The function will also check if the RCRD CPY directory exists. If not, it will return None.
    rcrd_cpy_dir = os.path.join(project_dir, discipline, "RCRD CPY")
    return rcrd_cpy_dir if os.path.exists(rcrd_cpy_dir) else None


def scan_directory(rcrd_cpy_dir: str, cutoff_date: datetime.datetime) -> list:
    """Scans the RCRD CPY directory for recently modified files and returns their directories."""
    # The input to this function is a single directory path to a RCRD CPY folder and a cutoff date.
    # This function will scan the RCRD CPY directory for files modified since the cutoff date.
    # If a file is found that meets the criteria, the directory containing the file will be added to the matching_dirs set.
    # The function will return a list of directories that contain modified files.

    modified_dirs = set()
    stack = [rcrd_cpy_dir]
    try:
        while stack:
            current_dir = stack.pop()
            try:
                with os.scandir(current_dir) as entries:
                    for entry in entries:
                        if entry.is_file():
                            file_mod_time = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
                            if file_mod_time >= cutoff_date:
                                modified_dirs.add(current_dir)
                                logging.info(f"Modified file found: {entry.path}")
                                # Do not continue scanning this directory if a modified file is found
                                break
                        elif entry.is_dir():
                            stack.append(entry.path)
            except PermissionError:
                logging.warning(f"Permission denied: {current_dir}, skipping.")
            except FileNotFoundError:
                logging.warning(f"Directory not found: {current_dir}, skipping.")

        return list(modified_dirs)

    except Exception as e:
        logging.warning(f"Skipping {rcrd_cpy_dir}: {e}")
        return []


def master_dict_to_dataframe(master_dict: dict) -> pd.DataFrame:
    """Converts a nested dictionary into a Pandas DataFrame."""
    # Convert a nested dictionary (master_dict) into a structured pandas DataFrame.
    # The master_dict is of the form {Office: {Discipline: [Matching Directories]}}
    # The DataFrame will have columns for Office, Discipline, and Path.
    data = [
        (office, discipline, path)
        for office, disciplines in master_dict.items()
        for discipline, paths in disciplines.items()
        for path in paths
    ]
    return pd.DataFrame(data, columns=["Office", "Discipline", "Path"])


def main():
    # clear command line
    os.system('cls' if os.name == 'nt' else 'clear')

    # Set up master dictionary with empty lists for each discipline in each office
    master_dict = {office: {discipline: [] for discipline in disciplines} for office in offices}

    # Set the cutoff date for the scan
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_threshold)

    # Get the office directories
    office_dirs = get_office_dirs(base_dir, offices) # {"SSC": \\adgce.local\projects\SSC}

    # Get the project group directories
    for office, office_dir in office_dirs.items():
        project_group_dirs = get_subdirectories(office_dir, filter_digits=5) # [\\adgce.local\projects\SSC\project group number]
        project_group_dirs = [] if (project_group_dirs is None) else project_group_dirs
        # Get the project directories
        for project_group_dir in project_group_dirs:
            project_dirs = get_subdirectories(project_group_dir, filter_digits=None) # [\\adgce.local\projects\SSC\25000\25633]
            # Get the RCRD CPY directories for each discipline and collect in a dictionary of the form
            # {Office: {Discipline: [Matching Directories]}}}}
            for project_dir in project_dirs:
                for discipline in disciplines:
                    rcrd_cpy_dir = get_rcrd_cpy_dirs(discipline, project_dir) # \\adgce.local\projects\SSC\25000\25633\CVL\RCRD CPY
                    if rcrd_cpy_dir:
                        mod_dirs = scan_directory(rcrd_cpy_dir, cutoff_date) # [\\adgce.local\projects\SSC\25000\25633\CVL\RCRD CPY\files]
                        # print(f"Modified directories for {office} {discipline} {project_dir}: {mod_dirs}")
                    else:
                        mod_dirs = []
                        # print(f"No RCRD CPY directory found for {office} {discipline}")
                    master_dict[office][discipline].extend(mod_dirs)

    # Write raw master_dict results to json
    with open("recently_issued_folders.json", "w") as f:
        json.dump(master_dict, f, indent=4)

    # Convert master_dict to a DataFrame
    df = master_dict_to_dataframe(master_dict)
    print(df)

    # Write DataFrame to CSV
    df.to_csv("recently_issued_folders.csv", index=False)

    logging.info("Scanning completed successfully. Results saved.")

if __name__ == "__main__":
    main()