import os
import datetime
import pandas as pd
import json, csv

# CONTINUE IN LINE 120

def main():
    # clear command line
    os.system('cls' if os.name == 'nt' else 'clear')

    # The purpose of this script is to show which disciplines on which projects have modified files
    # in their RCRD CPY directories within the last 30 days.
    # Define the base directories to scan. 
    # All projects located in \\adgce.local\projects.
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
    

    base_dir = r"\\adgce.local\projects"
    # Choose offices and disciplines to scan, as well as the number of days to look back
    offices = ["SSC"]
    disciplines = ["CVL"]
    days_threshold = 25

    # Set up master dictionary with empty lists for each discipline in each office
    master_dict = {}
    for office in offices:
        master_dict[office] = {}
        for discipline in disciplines:
            master_dict[office][discipline] = []

    # Set the cutoff date for the scan
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_threshold)


    def get_office_dirs(base_dir: str, offices: list):
        # The input to this function is a base directory and a list of office short names (SSC, GLC, etc.).
        # This function will return a dictionary of directories for office folders in the base directory. 
        # The dict will be of the form {"SSC": \\adgce.local\projects\SSC}
        office_dirs = {}
        for office in offices:
            office_dirs[office] = os.path.join(base_dir, office)
            # print("Office directory: ", office_dirs[office])
        return office_dirs

    def get_project_group_dirs(office_dir):
        # The input to this function is a single office directory
        # This function will return a list of directories for project group folders in the office directory. 
        # The list will be of the form [\\adgce.local\projects\SSC\project group number]
        project_group_dirs = []
        with os.scandir(office_dir) as entries:
            for entry in entries:
                # Check that the folder has a 5-digit name
                if entry.is_dir() and len(entry.name) == 5 and entry.name.isdigit():
                    project_group_dirs.append(entry.path)
                    # print("Project Group directory: ", entry.path)
        # print(f"Project Group directories: {project_group_dirs}")
        return project_group_dirs


    def get_project_dirs(project_group_dir):
        # The input to this function is a single project group directory
        # This function will return a list of directories for project folders in the project group directory. 
        # The list will be of the form [\\adgce.local\projects\SSC\25000\25633]
        # For each directory, this function will also check that it is a project directory
        project_dirs = []
        with os.scandir(project_group_dir) as entries:
            for entry in entries:
                if entry.is_dir():
                    project_dirs.append(entry.path)
                    # print("Project directory: ", entry.path)
        return project_dirs
    

    def get_rcrd_cpy_dirs(discipline, project_dir):
        # The input to this function is a single discipline and a single project directory
        # This function will return the directory for the RCRD CPY folder in the project directory.
        # The directory will be of the form \\adgce.local\projects\SSC\25000\25633\CVL\RCRD CPY
        # The function will also check if the RCRD CPY directory exists. If not, it will return None.
        rcrd_cpy_dir = os.path.join(project_dir, discipline, "RCRD CPY")
        if os.path.exists(rcrd_cpy_dir):
            return rcrd_cpy_dir
        else:
            return None


    def scan_directory(rcrd_cpy_dir, cutoff_date):
        # The input to this function is a single directory path to a RCRD CPY folder and a cutoff date.
        # This function will scan the RCRD CPY directory for files modified since the cutoff date.
        # If a file is found that meets the criteria, the directory containing the file will be added to the matching_dirs set.
        # The function will return a list of directories that contain modified files.

        modified_dirs = []
        try:
            with os.scandir(rcrd_cpy_dir) as entries:
                for entry in entries:
                    if entry.is_file():
                        file_mod_time = datetime.datetime.fromtimestamp(entry.stat().st_mtime)
                        if file_mod_time >= cutoff_date:
                            modified_dirs.append(os.path.dirname(entry.path))
                            print(f"Modified file: {entry.path}")
                            return modified_dirs
                    elif entry.is_dir():
                        tmp_modified_dirs = scan_directory(entry.path, cutoff_date)
                        if tmp_modified_dirs:
                            modified_dirs.extend(tmp_modified_dirs)  # Recurse into subdirectories
            return modified_dirs
        except Exception as e:
            print(f"Skipping {rcrd_cpy_dir}: {e}")
            return []
        

    def master_dict_to_dataframe(master_dict: dict) -> pd.DataFrame:
    # Convert a nested dictionary (master_dict) into a structured pandas DataFrame.
    # The master_dict is of the form {Office: {Discipline: [Matching Directories]}}
    # The DataFrame will have columns for Office, Discipline, and Path.
        data = []
        for office, disciplines in master_dict.items():
            for discipline, paths in disciplines.items():
                for path in paths:
                    data.append([office, discipline, path])
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=["Office", "Discipline", "Path"])
        return df

    # Get the office directories
    office_dirs = get_office_dirs(base_dir, offices) # {"SSC": \\adgce.local\projects\SSC}
    # print(f"Office directories: {office_dirs}")

    # Get the project group directories
    for office, office_dir in office_dirs.items():
        project_group_dirs = get_project_group_dirs(office_dir) # [\\adgce.local\projects\SSC\project group number]
        # Get the project directories
        for project_group_dir in project_group_dirs:
            project_dirs = get_project_dirs(project_group_dir) # [\\adgce.local\projects\SSC\25000\25633]
            # print(f"Project directories for {office}: {project_dirs}")

            # CONTINUE HERE
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

if __name__ == "__main__":
    main()