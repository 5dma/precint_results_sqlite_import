# Precinct Results Importer to SQLite

Maryland's Board of Elections provides precinct-level results in CSV files. This Python script imports that CSV file into an SQLite database.

## System requirements
* Python 3
* SQLite 3

## CSV file requirements
The following headings are required in the CSV file:
* Election District - Precinct
* Congressional
* Legislative
* Office Name
* Office District
*Candidate Name
* Party
* Winner
* Write-In?
* Early Votes
* Early Votes Against
* Election Night Votes
* Election Night Votes Against
* Mail-In Ballot 1 Votes
* Mail-In Ballot 1 Votes Against
* Provisional Votes
* Provisional Votes Against
* Mail-In Ballot 2 Votes
* Mail-In Ballot 2 Votes Against


## Running this script
`python3 import_to_sqlite.py directory_for_sqlite_db path_to_csv_file`
