import subprocess
import os
import sys
import sqlite3
import hashlib

repo_path = subprocess.check_output(["git", "rev-parse", "--show-toplevel"])

# folder to store all settings and backups
common_path = os.path.expanduser("~/Library/Application Support/git-undo/")

# make sure the settings and backups folder exists
if not os.path.isdir(common_path):
  os.mkdir(common_path)

conn = sqlite3.connect(common_path + 'gitundo.db')
cursor = conn.cursor()

# Create table
cursor.execute('''CREATE TABLE IF NOT EXISTS backups
	(backupid integer primary key autoincrement, repo_path text, created_at timestamp, git_command text)''')

created_at = int(time.time() * 1000)
git_command = "git " + sys.argv[1:].join(" ")

cursor.execute('''INSERT INTO backups (repo_path, created_at, git_command) VALUES (?, ?, ?)''',
	(repo_path, created_at, git_command))

backupid = cursor.lastrowid

print "backed up with id: " + backupid

sys.stdout.flush()

conn.commit()
conn.close()

subprocess.call(["git"] + sys.argv[1:])