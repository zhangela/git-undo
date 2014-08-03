import subprocess
import os
import sys
import sqlite3
import hashlib
import time

# strip new line
repo_path = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).strip()

# folder to store all settings and backups
common_path = os.path.expanduser("~/Library/Application Support/git-undo/")

# make sure the settings and backups folder exists
if not os.path.isdir(common_path):
  os.mkdir(common_path)

def backup():

	conn = sqlite3.connect(common_path + 'gitundo.db')
	cursor = conn.cursor()

	# Create table
	cursor.execute('''CREATE TABLE IF NOT EXISTS backups
		(backupid integer primary key autoincrement, repo_path text, created_at timestamp, git_command text)''')

	created_at = int(time.time() * 1000)
	git_command = "git " + " ".join(sys.argv[1:])

	cursor.execute('''INSERT INTO backups (repo_path, created_at, git_command) VALUES (?, ?, ?)''',
		(repo_path, created_at, git_command))

	backupid = cursor.lastrowid

	print "backed up with id: " + str(backupid)

	sys.stdout.flush()

	conn.commit()
	conn.close()

# returns commit id of the previous commit
def getLastCommit():
	counter = 2
	x = subprocess.check_output(["git"]+["log"])
	y = x.split('\n')
	for i in y:
		temp = i.split()
		if temp==[]:
			continue
		elif (temp[0]=="commit"):
			counter-=1

		if counter==0:
			return temp[1]
	return False	

# returns commit id latest commit
def getCurrentCommit():
	x = subprocess.check_output(["git"]+["log"])
	y = x.split('\n')
	for i in y:
		temp = i.split()
		if (temp[0]=="commit"):
			return temp[1]
	return False	

# returns curent branch
def getBranch():
	x = subprocess.check_output(["git"]+["branch"])
	y = x.split('\n')
	for i in y:
		if (i[:1]=="*"):
			return i[2:]
	return False



def undo():
	repo_path = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).strip()
	conn = sqlite3.connect(common_path + 'gitundo.db')
	cursor = conn.cursor()

	# cursor.execute('''INSERT INTO backups (repo_path, created_at, git_command) VALUES (?, ?, ?)''',
	# 	(repo_path, created_at, git_command))
	# Create table
	action_to_be_undone = cursor.execute('''SELECT * from backups where created_at=
		(select max(created_at) from backups where repo_path=\"''' +  
			repo_path + '''\") and repo_path=\"''' + repo_path + '''\";''')

	for row in action_to_be_undone:
		print row
	sys.stdout.flush()



# undos push, as noted by http://stackoverflow.com/questions/1270514/undoing-a-git-push
def undoPush():
	# if system.denyNonFastForwards and denyDeletes:
	if False:
		subprocess.call(["git","update-ref","refs/heads/"+getBranch(),getLastCommit(),getCurrentCommit()])
	# elif system.denyNonFastForwards and master is not the only branch
	elif False:
		print("")
	# elif system.denyNonFastForwards
	elif False:
		subprocess.call(["git","push","origin",":"+getBranch()])
		subprocess.call(["git","push","origin",getLastCommit()+":refs/heads/"+getBranch()])
	# else
	else:
 		subprocess.call(["git","push","-f","origin",getLastCommit()+":"+getBranch()])


## Main Code
if sys.argv[1] == "undo":
	undo()
# elif (sys.argv[1] == "push"):
# 	undoPush()
else:
	backup()
	subprocess.call(["git"] + sys.argv[1:])


prompt = '> '

## Code for prompts

# print("Your repository has a denyNonFastForward flag on, so the history \
# 	cannot be overwritten. The undo-push will be written into the git history.\
# 	 Is that alright? (Y/N)")
# ans = raw_input(prompt)
# if (ans.lower()=="y" or ans.lower()=="yes"):
# elif (ans.lower()=="n" or ans.lower()=="no"):
# else:
# 	raise ValueError("Sorry bro I have no idea what you're saying.  Bye.")
