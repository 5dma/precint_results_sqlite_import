# Imports a state Board of Elections into SQLITE.


import sys
import csv
import sqlite3
import os.path

if len(sys.argv) < 3:
	print("Usage: python3 import_to_sqlite.py <sqlite_directory> <csv_file>")
	sys.exit()


original_file_path = sys.argv[2]
if not os.path.isfile(original_file_path):
		print("No such file {0}. Exiting.".format(original_file_path))
		sys.exit()

target_directory = sys.argv[1]
db_filename = "precinct_results.sqlite"
db_path = target_directory + "/" + db_filename

if os.path.isdir(target_directory):	
	if os.path.exists(db_path):
		print("A database {0} already exists in {1}. Exiting.".format(db_filename, target_directory))
		sys.exit()

else:
	os.mkdir(target_directory)



print("Removing trailing blanks in CSV file...")
original_file = open(original_file_path, "r")
clean_file_path = '/tmp/input_file.csv'
clean_file = open(clean_file_path, "w")

lines = original_file.readlines()
for line in lines:
	stripped_line = line.rsplit(' ',1)
	clean_file.write(stripped_line[0] + "\n")
clean_file.close()
original_file.close()


print("Creating database...")

con = sqlite3.connect(db_path)
cur = con.cursor()
cur.execute("CREATE TABLE office_names (ID INTEGER PRIMARY KEY AUTOINCREMENT,office_name TEXT)")
cur.execute("CREATE TABLE candidate_names (ID INTEGER PRIMARY KEY AUTOINCREMENT, candidate_name TEXT)")
cur.execute("CREATE TABLE party_names (ID INTEGER PRIMARY KEY AUTOINCREMENT,party_name TEXT)")
cur.execute("CREATE TABLE election_districts (ID INTEGER PRIMARY KEY AUTOINCREMENT,election_district TEXT)")

big_create = """
CREATE TABLE results (
	ID INTEGER PRIMARY KEY AUTOINCREMENT,
	Election_District_Precinct REFERENCES election_districts (ID),
	Congressional INTEGER,
	Legislative TEXT,
	Office_Name INTEGER REFERENCES office_names (ID),
	Office_District TEXT,
	Candidate_Name INTEGER REFERENCES office_names (ID),
	Party INTEGER REFERENCES office_names (ID),
	Winner INTEGER DEFAULT(0),
	Write_IN INTEGER DEFAULT(0),
	Early_Votes INTEGER DEFAULT(0),
	Early_Votes_Against INTEGER DEFAULT(0),
	Election_Night_Votes INTEGER DEFAULT(0),
	Election_Night_Votes_Against INTEGER DEFAULT(0),
	Mail_In_Ballot_1_Votes INTEGER DEFAULT(0),
	Mail_In_Ballot_1_Votes_Against INTEGER DEFAULT(0),
	Provisional_Votes INTEGER DEFAULT(0),
	Provisional_Votes_Against INTEGER DEFAULT(0),
	Mail_In_Ballot_2_Votes INTEGER DEFAULT(0),
	Mail_In_Ballot_2_Votes_Against INTEGER DEFAULT(0)
)
"""
cur.execute(big_create)


election_districts = []
office_names = []
candidate_names = []
party_names = []

print("Adding entries to auxiliary tables...")

with open(clean_file_path, mode='r') as file:
	csv_file = csv.DictReader(file,None,None, dialect='unix', delimiter=',', lineterminator=' \r', quoting=csv.QUOTE_ALL)
	for lines in csv_file:
		# Check for new election district-precinct
		current_election_precinct = lines["Election District - Precinct"]
		if current_election_precinct not in election_districts:
			election_districts.append(current_election_precinct)
			insert_statement = 'INSERT INTO election_districts (election_district) VALUES ("{0}")'.format(current_election_precinct)
			cur.execute(insert_statement)
		# Check for new office name
		current_office_name = lines["Office Name"]
		if current_office_name not in office_names:
			office_names.append(current_office_name)
			insert_statement = 'INSERT INTO office_names (office_name) VALUES ("{0}")'.format(current_office_name)
			cur.execute(insert_statement)
		# Check for new candidate name
		current_candidate_name = lines["Candidate Name"]
		current_candidate_name = current_candidate_name.replace('"', '') 
		if current_candidate_name not in candidate_names:
			candidate_names.append(current_candidate_name)
			insert_statement = 'INSERT INTO candidate_names (candidate_name) VALUES ("{0}")'.format(current_candidate_name)
			cur.execute(insert_statement)
		# Check for new party name
		current_party = lines["Party"] 
		if current_party not in party_names:
			party_names.append(current_party)
			insert_statement = 'INSERT INTO party_names (party_name) VALUES ("{0}")'.format(current_party)
			cur.execute(insert_statement)
		

	con.commit()
	cur.execute("CREATE UNIQUE INDEX idx_candidate_name ON candidate_names(candidate_name)")
	cur.execute("CREATE UNIQUE INDEX idx_election_district ON election_districts(election_district)")
	cur.execute("CREATE UNIQUE INDEX idx_office_name ON office_names(office_name)")
	cur.execute("CREATE UNIQUE INDEX idx_party_name ON party_names(party_name)")
	
	file.seek(0)
	
	print("Adding entries to main results table...")
	csv_file = csv.DictReader(file,None,None, dialect='unix', delimiter=',', quoting=csv.QUOTE_ALL)
	for lines in csv_file:

		# Get election_district ID
		select = 'SELECT ID FROM election_districts WHERE election_district="{0}"'.format(lines["Election District - Precinct"])
		cur.execute(select)
		res = cur.fetchone()
		election_district_id = res[0]

		
		# Get office_name ID
		select = 'SELECT ID FROM office_names WHERE office_name="{0}"'.format(lines["Office Name"])
		cur.execute(select)
		res = cur.fetchone()
		office_id = res[0]

		# Get candidate_name ID
		current_candidate_name = lines["Candidate Name"];
		current_candidate_name = current_candidate_name.replace('"', '') 		
		select = 'SELECT ID FROM candidate_names WHERE candidate_name="{0}"'.format(current_candidate_name)
		cur.execute(select)
		res = cur.fetchone()
		candidate_id = res[0]


		# Get party_name ID
		select = 'SELECT ID FROM party_names WHERE party_name="{0}"'.format(lines["Party"])
		cur.execute(select)
		res = cur.fetchone()
		party_id = res[0]


		big_insert = """
			INSERT INTO results (Election_District_Precinct,Congressional,Legislative,Office_Name,Office_District,Candidate_Name,Party,Winner,Write_IN,Early_Votes,Early_Votes_Against,Election_Night_Votes,Election_Night_Votes_Against,Mail_In_Ballot_1_Votes,Mail_In_Ballot_1_Votes_Against,Provisional_Votes,Provisional_Votes_Against,Mail_In_Ballot_2_Votes,Mail_In_Ballot_2_Votes_Against) VALUES ({0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18})
		"""


		big_insert_command = big_insert.format(
			election_district_id,
			lines["Congressional"],
			'"' + lines["Legislative"] + '"',
			office_id,
			"NULL" if lines["Office District"] == "" else '"' + lines["Office District"] + '"',
			candidate_id,
			party_id,
			1 if lines["Winner"] == "Y" else 0,
			1 if lines["Write-In?"] == "Y" else 0,
			0 if lines["Early Votes"] == " " else lines["Early Votes"],
			0 if lines["Early Votes Against"] == "" else lines["Early Votes Against"],
			0 if lines["Election Night Votes"] == "" else lines["Election Night Votes"],
			0 if lines["Election Night Votes Against"] == "" else lines["Election Night Votes Against"],
			0 if lines["Mail-In Ballot 1 Votes"] == "" else lines["Mail-In Ballot 1 Votes"],
			0 if lines["Mail-In Ballot 1 Votes Against"] == "" else lines["Mail-In Ballot 1 Votes Against"],
			0 if lines["Provisional Votes"] == "" else lines["Provisional Votes"],
			0 if lines["Provisional Votes Against"] == "" else lines["Provisional Votes Against"],
			0 if lines["Mail-In Ballot 2 Votes"] == "" else lines["Mail-In Ballot 2 Votes"],
			0 if lines["Mail-In Ballot 2 Votes Against"] == "" else lines["Mail-In Ballot 2 Votes Against"]
		)
		cur.execute(big_insert_command)
	con.commit()

	print("Creating indexes...")
	cur.execute("CREATE INDEX idx_candidate_id ON results(Candidate_Name)")
	cur.execute("CREATE INDEX idx_office_id ON results(Office_Name)")
	cur.execute("CREATE INDEX idx_precinct ON results(Election_District_Precinct)")
		
file.close()
cur.close()
con.close()
print("All done! Use the database by running sqlite3 " + db_path)