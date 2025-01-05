# -*- coding: utf-8 -*-
"""Staging Database

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1KP8Dzg5sqKZM4QGi_NZC5myJYs1NAc3S
"""

!pip install mysql-connector-python
from google.colab import drive

# Mount Google Drive
drive.mount('/content/drive')

"""# db.py"""

import mysql.connector as mysql

# Connect to the Amazon RDS MySQL database and set the default schema to 'cms'
db = mysql.connect(
    host='wm-capstone-db.cviy020ogwh2.us-east-2.rds.amazonaws.com',  # RDS endpoint
    user='benuehlinger',  # Master username
    password='WMCapstone1!',  # Master password
    database='cms',  # Default schema set to 'cms'
    port=3306  # MySQL port
)

# Set autocommit to True for immediate data changes
db.autocommit = True

# Create cursor objects for executing SQL queries
cur = db.cursor(buffered=False)
curp = db.cursor(prepared=True)

# # Ensure the 'cms' schema exists (create it if not already present)
# cur.execute("CREATE SCHEMA IF NOT EXISTS cms;")
# cur.execute("USE cms;")  # Switch to the 'cms' schema explicitly

# Test the connection
try:
    print("Connected to the 'cms' schema successfully!")
except mysql.Error as e:
    print(f"Error: {e}")

"""# I needed, drop all tables loaded (temp%, cms_tables, load_log)"""

# Step 1: Query to find tables that match the criteria
cur.execute("""
    SELECT GROUP_CONCAT(table_name)
    FROM information_schema.tables
    WHERE table_schema = 'cms'
    AND (table_name LIKE 'temp%' OR table_name IN ('cms_tables', 'load_log'));
""")

# Step 2: Fetch the result to handle cases where no tables are found
result = cur.fetchone()
if result[0] is None:  # No tables match the criteria
    print("No tables to drop.")
else:
    tables = result[0]  # Tables to drop as a comma-separated list

    # Step 3: Prepare and execute the DROP TABLE query dynamically
    drop_query = f"DROP TABLE IF EXISTS {tables};"
    cur.execute(drop_query)
    print(f"Dropped tables: {tables}")

"""Name directory for which folders of past data exist

# Create necessary folder directory if doesnt exist
"""

import os

# Path to the DataDir folder where folders will be created
dataDirs = '/content/drive/My Drive/Capstone Project/Staging Database/DataDir'

# List of folder names to create based on your data time periods
# folders = [
#     "24Oct", "24Jul", "24Apr", "24Jan",
#     "23Nov", "23Oct", "23Jul", "23Apr", "23Jan",
#     "22Oct", "22Jul", "22Apr", "22Jan",
#     "21Oct", "21Jul", "21Apr", "21Mar", "21Jan",
#     "20Oct", "20Jul", "20Apr", "20Jan",
#     "19Oct", "19Jul", "19Apr", "19Mar",
#     "18Oct", "18Jul", "18May", "18Jan",
#     "17Oct", "17Jul", "17Apr"
# ]

# # Create folders in DataDir
# for folder in folders:
#     folder_path = os.path.join(DataDir, folder)
#     try:
#         os.makedirs(folder_path, exist_ok=True)  # Create folder if it doesn't exist
#         print(f"Created folder: {folder_path}")
#     except Exception as e:
#         print(f"Error creating folder {folder_path}: {e}")

"""# load_all"""

import os  # For path operations
import glob  # For file searching
import re  # For regex operations
import csv  # For reading CSV files

# Ensure load_log table exists
try:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS load_log (
            tempName VARCHAR(255),
            fileName VARCHAR(255),
            origName VARCHAR(255),
            tblStatus VARCHAR(50),
            errMessage TEXT,
            loadTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Table `load_log` ensured to exist.")
except Exception as e:
    print(f"Error ensuring `load_log` exists: {e}")

# Path to the directory containing your files
Home = '/content/drive/My Drive/Capstone Project/Staging Database'
DataDir = os.path.join(Home, 'DataDir')  # Path to the DataDir folder

# Useful CSVs found in LOAD.TXT
load_txt_path = os.path.join(Home, 'LOAD.txt')
with open(load_txt_path, 'r') as f:
    CSV = [l.rstrip().lower() for l in f.readlines()]  # Filter list from LOAD.txt

# Load CSVs into MySQL tables
dataDirs = [os.path.join(DataDir, folder) for folder in os.listdir(DataDir) if os.path.isdir(os.path.join(DataDir, folder))]
tblCount = 0  # Initialize the table counter

for folder in dataDirs:
    print(f"** Processing folder: {folder} **")

    csv_files = glob.glob(f'{folder}/*.csv')  # Find all CSV files in the current folder
    for fname in csv_files:
        m = re.search('(.+?)\\.csv', os.path.basename(fname))  # Extract base name of the CSV file
        nm = m.groups()[0]

        # Filter based on LOAD.TXT
        if nm.lower() not in CSV:
            print(f"Skipping {fname}, not listed in LOAD.txt.")
            continue

        print(f"Processing {fname}")
        f = open(fname, 'r')
        csvfile = csv.DictReader(f)
        try:
            tblCount += 1
            try:
                cur.execute(f'DROP TABLE IF EXISTS `{nm}`')  # Drop table if it exists
            except Exception as drop_err:
                print(f"Warning: Unable to drop table `{nm}`. Continuing...")

            tblnm = f"temp{tblCount}"  # Temporary table name
            q = f'CREATE TABLE `{tblnm}` ('
            q += ','.join(f'`{col}` VARCHAR(255)' for col in csvfile.fieldnames)  # Create columns based on CSV headers
            q += ')'
            cur.execute(q)
            cur.execute(f'ALTER TABLE `{tblnm}` ADD CMS_Data_ID VARCHAR(20)')
            cur.execute(
                "INSERT INTO load_log (tempName, fileName, origName, tblStatus, errMessage) VALUES (%s, %s, %s, %s, NULL)",
                (tblnm, fname, nm, 'empty')
            )
        except Exception as err:
            print(f"\tERR: Could not create {tblnm} .. skipping")
            print(f"\t{str(err)}")
            cur.execute(
                "INSERT INTO load_log (tempName, fileName, origName, tblStatus, errMessage) VALUES (%s, %s, %s, NULL, %s)",
                (tblnm, fname, nm, str(err))
            )
            continue

        rows = [row for row in csvfile]
        f.close()
        for r in rows:
            r['CMS_Data_ID'] = folder  # Add folder metadata
        rows = [rows[i:(i + 5000)] for i in range(0, len(rows), 5000)]  # Split into batches of 5000

        try:
            print("\t", end='')
            for batch in rows:
                q = f'INSERT INTO `{tblnm}` VALUES '
                q += ','.join([str(tuple(i.values())) for i in batch])  # Insert rows
                cur.execute(q)
                print(".", end='')
            print("")

            cur.execute(f"UPDATE load_log SET tblStatus='loaded' WHERE tempName='{tblnm}'")
        except Exception as err:
            cur.execute(
                "UPDATE load_log SET errMessage=%s WHERE tempName=%s", (str(err), tblnm)
            )

db.close()

# ** run rename_tables.sql
#   Fuzzy match table names
#   Merge same tables
#   Rename to sane tables

"""# Match Tables"""

# -*- coding: utf-8 -*-
"""
Try to fuzzy match tables
    - Find candidates
    - Check structure
    - Merge
    - Rename

"""

# from db import *

#with open('load.txt','r') as f:
#    CSV = [l.rstrip().lower() for l in f.readlines()]

# Drop unneeded tables. Heuristic.
q = """select tempName
	from load_log
 where
	NOT (fileName like '%hospital%'
    or fileName like '%decimal%'
    or fileName like '%va_te%'
    or fileName like '%hvbp%')
    or fileName like '%state%'
    or fileName like '%national%'
    or filename like '%quarterly%'
    or filename like '%quality%'
    or filename like 'PCH%'
    or filename like '%reduction%'
    or filename like '%readmission%'
    or filename like '%spending%'
    or filename like '%payment%'
    or filename like '%measure%'
    """
cur.execute(q)
altersql = [f"alter table cms.`{row[0]}` rename cms_unused.`{row[0]}`" for row in cur.fetchall()]
for q in altersql:
    try:
        cur.execute(q)
    except:
        pass
db.commit()

try:
    cur.execute('drop table cms_unused.load_log')
    q = """create table cms_unused.load_log as
    select * from load_log
    where tempName in (
    select table_name from information_Schema.tables
    	where table_schema = 'cms_unused')"""
    cur.execute(q)
except:
    pass

# Remove deleted tables from log
q = """delete from load_log
  where not exists (select 'x' from information_schema.tables where table_schema = 'cms' and table_name = tempName);"""
cur.execute(q)
db.commit()

# Fuzzy Match tables using levenshtein
cur.execute('call cms.match_tables')




# # cur.execute('select tblName from cms_tables')
# # CSV = [row[0] for row in cur.fetchall()]

# # cur.execute('select tempName,fileName from load_log')
# # cur.fetchall()

# fig,(ax1,ax2) = plt.subplots(2,dpi=120)

# fig.tight_layout(pad=3)
# ax1.hist(df2['Score'],bins=30)
# ax1.set_title('CABG Mortality CMSApr21 Data')
# ax1.axvline(x=5.4,color='k',ls=':')
# ax1.set_xlabel('Score')
# ax1.set_ylabel('Number of Facilities')
# #plt.text()

# ax2.hist(df2['den'],bins=30)
# ax2.set_title('CABG Volumes CMSApr21 Data')
# ax2.axvline(x=134,color='k',ls=':')
# ax2.set_xlabel('CABG Volume')
# ax2.set_ylabel('Number of Facilities')
# #plt.text()

# plt.scatter(df2['den'],df2['Score'],s=3)
# plt.title('CABG Volume vs CABG Mortality Score')