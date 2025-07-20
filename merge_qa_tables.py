### This script takes a csv file and an excel file as input and merges them into a single table. Both files will contain a list of directories.
### The program should identify the directories in the CSV file that are not in the Excel file and output them to a new CSV file.

### Workflow: 
# 1 - Copy sheet from teams into "tmp_excel_for_teams.xlsx".
# 2 - Run filescan.py to get the list of directories in the CSV file "recently_issued_folders.csv".
# 3 - Run this script to merge the two files into a new CSV file "merged_output.csv".
# 4 - Copy the "merged output.csv" directories into the excel on teams.

import pandas as pd
import os
import openpyxl
from openpyxl import load_workbook
import logging

MONTH = "July" # This will be used to read the correct tab from the Excel file.
CSV_FILE_PATH = r"C:/Users/fsaniter/OneDrive - ADG/Desktop/Temp WIP Files/00_QA stuff/adg-qa-check/recently_issued_folders.csv"
EXCEL_FILE_PATH = r"C:/Users/fsaniter/OneDrive - ADG/Desktop/Temp WIP Files/00_QA stuff/adg-qa-check/tmp_excel_for_merging.xlsx"
NEW_CSV_FILE_PATH = r"C:/Users/fsaniter/OneDrive - ADG/Desktop/Temp WIP Files/00_QA stuff/adg-qa-check/merged_output.csv"

def read_csv_file(file_path: str) -> pd.DataFrame:
    """Reads a CSV file and returns a DataFrame."""
    try:
        df = pd.read_csv(file_path)
        logging.info(f"CSV file read successfully: {df}")
        return df
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        return pd.DataFrame()
    
def read_excel_file(file_path: str, tab_name: str) -> pd.DataFrame:
    """Reads an Excel file and returns a DataFrame corresponding to the specified tab name."""
    try:
        df = pd.read_excel(file_path, sheet_name=tab_name)
        logging.info(f"Excel file read successfully: {df}")
        return df
    except Exception as e:
        logging.error(f"Error reading Excel file: {e}")
        return pd.DataFrame()
    

def merge_dataframes(csv_df: pd.DataFrame, excel_df: pd.DataFrame) -> pd.DataFrame:
    """Merges the 2 dataframes into a new dataframes that contains only the rows from csv_df, in which the 'Path' column is not present in excel_df."""
    try:
        merged_df = csv_df[~csv_df['Path'].isin(excel_df['Path'])]
        logging.info(f"Dataframes merged successfully: {merged_df}")
        return merged_df
    except Exception as e:
        logging.error(f"Error merging dataframes: {e}")
        return pd.DataFrame()


def write_csv_file(file_path: str, df: pd.DataFrame):
    """Writes a DataFrame to a CSV file."""
    try:
        df.to_csv(file_path, index=False)
    except Exception as e:
        logging.error(f"Error writing CSV file: {e}")
    

def main():

    month = MONTH
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    csv_file_path = CSV_FILE_PATH
    excel_file_path = EXCEL_FILE_PATH
    new_csv_file_path = NEW_CSV_FILE_PATH
    excel_tab_name = month

    csv_df = read_csv_file(csv_file_path)
    excel_df = read_excel_file(excel_file_path, excel_tab_name)

    new_df = merge_dataframes(csv_df, excel_df)
    write_csv_file(new_csv_file_path, new_df)
    logging.info(f"Output written to {new_csv_file_path}")


if __name__ == "__main__":
    main() 
