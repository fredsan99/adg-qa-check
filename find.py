import os

def find_files_containing_string(directory, search_string):
    """
    Search for files in the specified directory that contain a given string in their filenames.
    
    :param directory: Directory to search in
    :param search_string: String that filenames should contain
    :return: List of file paths containing the specified string
    """
    matching_files = []

    # Walk through the directory
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if search_string in filename:
                matching_files.append(os.path.join(dirpath, filename))
    
    return matching_files

if __name__ == "__main__":
    # Define the directory to search and the string to look for in filenames
    search_directory = "J:\\SSC"  # Update this path
    search_string = 'Jones'  # Replace with the string you're searching for in filenames

    # Find and list files containing the specified string in their filenames
    files = find_files_containing_string(search_directory, search_string)

    # Output the found files
    print(f"Files containing the string '{search_string}':")
    for file in files:
        print(file)