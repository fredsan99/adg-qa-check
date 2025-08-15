import os, datetime, logging
import pandas as pd
import json
from typing import Any, Iterable

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
# The script will look for files in the RCRD CPY directories that have been modified within the last X days.
# The end result will be a nested dictionary of the form:
# {Office: {Discipline: [Matching Directories]}}


# Configure logging for debugging purposes
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

base_dir = r"\\adgce.local\projects" # C:\Users\frede\Desktop\projects\ADG QA Script\test_dirs
offices = ["SSC"]
disciplines = ["CVL"]
days_threshold = 15 # The script will check for files modified up to this many days in the past. 
ind_projects_to_scan = {"SSC": [], "SYD": ["27868", "24324"]}  # This can be used to specify individual projects to scan, if needed.


def get_office_dirs(base_dir: str, offices: list) -> dict:
    # The input to this function is a base directory and a list of office short names (SSC, GLC, etc.).
    # This function will return a dictionary of directories for office folders in the base directory. 
    # The dict will be of the form {"SSC": \\adgce.local\projects\SSC}
    office_dirs = {office: os.path.join(base_dir, office) for office in offices}
    return office_dirs


def get_subdirectories(directory: str, filter_digits):
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
        return []
    except Exception as e:
        logging.warning(f"Skipping {directory}: {e}")
        return []


def assemble_ind_project_dirs(base_dir: str, ind_projects_to_scan: dict) -> dict[str, list[str]]:
    """Returns a dictionary of individual project directories to scan."""
    # The input to this function is a base directory and a dictionary of individual projects to scan.
    # This function will return a dictionary with lists of project directories inside each office directory.
    # The project folders are named after the project number given in the ind_projects_to_scan dict.
    ind_project_dirs = {}
    for office, projects in ind_projects_to_scan.items():
        office_dir = os.path.join(base_dir, office)
        ind_project_dirs[office] = []
        for project_no in projects:
            project_group_no = f"{project_no[:2]}000"
            project_dir = os.path.join(office_dir, project_group_no, project_no)
            if os.path.exists(project_dir):
                ind_project_dirs[office].append(project_dir)
            else:
                logging.warning(f"Project directory {project_dir} does not exist, skipping.")
    return ind_project_dirs


def get_project_dirs(base_dir: str, offices: list, ind_projects_to_scan: dict):
    """Returns a list of project directories for each office."""
    # The input to this function is a base directory, a list of offices and a dictionary of
    # individual projects to scan.
    # This function will return a dictionary with lists of project directories inside each office directory.
    # The project folders are expected to be either five-digit numbers or
    # subdirectories of project folders with a suffix .xxx, e.g. 27170.001).
    
    office_dirs = get_office_dirs(base_dir, offices) # Dictionary of office directories
    project_group_dirs: dict[str, list[str]] = {} # This will hold the project group directories for each office
    for office, office_dir in office_dirs.items():
        groups = get_subdirectories(office_dir, filter_digits=5)
        project_group_dirs[office] = [] if (groups is None) else groups
    
    project_dirs: dict[str, list[str]] = {}
    for office, group_dirs in project_group_dirs.items():
        project_dirs[office] = []
        for group_dir in group_dirs:
            projects = get_subdirectories(group_dir, filter_digits=5)
            if projects:
                project_dirs[office].extend(projects)

    # Now, assemble the individual project directories for each office and add to the dict
    ind_project_dirs = assemble_ind_project_dirs(base_dir, ind_projects_to_scan)

    #Merge the individual project directories into the main project directories dictionary
    for office, ind_dirs in ind_project_dirs.items():
        if office in project_dirs:
            project_dirs[office].extend(ind_dirs)
        else:
            project_dirs[office] = list(ind_dirs)

    # The dict project_dirs now contains all project directories to scan under
    # each office under the old folder structure {"SSC": [list of project directories]}
    # Now check each project directory to see if it has sub-projects under the 
    # new folder structure (e.g. 27170\\27170.001\\CVL)
    for office, proj_dirs in project_dirs.items():
        sub_projects = []
        for proj_dir in proj_dirs:
            with os.scandir(proj_dir) as entries:
                for entry in entries:
                    if entry.is_dir() and len(entry.name) == 9 and entry.name[-4] == ".":
                        sub_project = entry.path
                        sub_projects.append(sub_project)
        if sub_projects:
            project_dirs[office].extend(sub_projects)    
    
    return project_dirs


def get_rcrd_cpy_dirs(discipline: str, project_dir: str):
    """Returns the RCRD CPY directory path if it exists."""
    # The input to this function is a single discipline and a single project directory
    # This function will return the directory for the RCRD CPY folder in the project directory.
    # The directory will be of the form \\adgce.local\projects\SSC\25000\25633\CVL\RCRD CPY
    # The function will also check if the RCRD CPY directory exists. If not, it will return None.
    rcrd_cpy_dir = os.path.join(project_dir, discipline, "RCRD CPY")
    return rcrd_cpy_dir if os.path.isdir(rcrd_cpy_dir) else None


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


def assemble_master_dict(disciplines: list, project_dirs: dict, cutoff_date) -> dict:
    """Assembles a master dictionary of directories for each office and discipline:
    {office: {discipline: {project_number: [paths]}}}"""
    # Set up master dictionary with empty lists for each discipline in each office
    master_dict = {office: {d: {} for d in disciplines} for office in project_dirs.keys()}

    for office, proj_dirs in project_dirs.items():
        for proj_dir in proj_dirs:
            proj_no = get_project_number_from_path(proj_dir)
            for discipline in disciplines:
                rcrd_cpy_dir = get_rcrd_cpy_dirs(discipline, proj_dir) # Single directory as string
                if rcrd_cpy_dir:
                    mod_dirs = scan_directory(rcrd_cpy_dir, cutoff_date) # [\\adgce.local\projects\SSC\25000\25633\CVL\RCRD CPY\files]
                    # print(f"Modified directories for {office} {discipline} {project_dir}: {mod_dirs}")
                else:
                    mod_dirs = []
                    # print(f"No RCRD CPY directory found for {office} {discipline}"):
                bucket = master_dict[office][discipline].setdefault(proj_no, [])
                bucket.extend(mod_dirs)
    return master_dict

def master_dict_to_dataframe(master_dict: dict, level_names: list[str], path_col="Path"):
    rows = []

    def walk(node, prefix):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, prefix + [str(k)])
        elif isinstance(node, list):
            for leaf in node:
                rows.append(prefix + [str(leaf)])
        else:
            # Fallback: treat scalar as a single leaf
            rows.append(prefix + [str(node)])

    walk(master_dict, [])

    if not rows:
        # Empty -> make a harmless empty frame
        key_cols = level_names or ["Level1"]
        return pd.DataFrame(columns=key_cols + [path_col])

    n_key_cols = len(rows[0]) - 1
    if level_names and len(level_names) != n_key_cols:
        raise ValueError(f"Only {len(level_names)} column names provided but {n_key_cols} column names required")

    cols = (level_names or [f"Level{i+1}" for i in range(n_key_cols)]) + [path_col]
    return pd.DataFrame(rows, columns=cols)


def get_project_number_from_path(path: str) -> str:
    """Extracts the project number from a given path."""
    # The input to this function is a path to a project directory.
    # This function will return the project number as a string.

    parts = os.path.normpath(path).split(os.sep)
    parts_enum = enumerate(parts)
    might_be_project_number = []
    for i, part in parts_enum:
        test = (part.isdigit() and len(part) == 5 and part[-3:] != "000")
        if test:
            might_be_project_number.append(part)
    if len(might_be_project_number) == 1:
        project_number = might_be_project_number[0]
    elif len(might_be_project_number) > 1:
        project_number = f"Multiple project numbers found: {might_be_project_number}"
    else:
        project_number = "No project number found"

    return project_number


def main():
    # clear command line
    os.system('cls' if os.name == 'nt' else 'clear')

    # Remove entries from ind_projects_to_scan that are already handled by 'offices'
    for office_key in list(ind_projects_to_scan.keys()):
        if office_key in offices:
            logging.info(f"Removing '{office_key}' from ind_projects_to_scan because it's already in offices")
            ind_projects_to_scan.pop(office_key, None)

    # Set the cutoff date for the scan
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_threshold)

    # Get the project directories
    project_dirs = get_project_dirs(base_dir, offices, ind_projects_to_scan)

    master_dict = assemble_master_dict(disciplines, project_dirs, cutoff_date)

    # Write raw master_dict results to json
    with open("recently_issued_folders.json", "w") as f:
        json.dump(master_dict, f, indent=4)

    # Convert master_dict to a DataFrame
    df = master_dict_to_dataframe(master_dict, level_names=["Office", "Discipline", "Project Number"], path_col="Path")
    print(df)

    # Write DataFrame to CSV
    df.to_csv("recently_issued_folders.csv", index=False)

    logging.info("Scanning completed successfully. Results saved.")

if __name__ == "__main__":
    main()