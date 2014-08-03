import subprocess
import os
import sys
import sqlite3
import time

def setup():
  global conn
  global cursor
  global repo_path
  global common_path
  global common_path_escaped

  # strip new line
  repo_path = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).strip()

  # folder to store all settings and backups
  common_path = os.path.expanduser("~/Library/Application Support/git-undo/")
  common_path_escaped = common_path.replace(" ", "\ ")

  # make sure the settings and backups folder exists
  if not os.path.isdir(common_path):
    os.mkdir(common_path)

  if not os.path.isdir(common_path + "backups"):
    os.mkdir(common_path + "backups")

  conn = sqlite3.connect(common_path + 'gitundo.db')
  cursor = conn.cursor()

  # all commands to ignore
  ignore = ["blame", "config", "describe", "diff", "log", "shortlog", "show", "status"]

def backup():
  # Create table
  cursor.execute('''CREATE TABLE IF NOT EXISTS backups
    (backupid integer primary key autoincrement, repo_path text, created_at timestamp, git_command text, most_recent integer)''')

  created_at = int(time.time() * 1000)
  git_command = "git " + " ".join(sys.argv[1:])

  #################### NEED TO UPDATE THIS!!!!
  cursor.execute('''DELETE FROM backups WHERE
    repo_path="%s" and created_at >
    (SELECT created_at FROM backups WHERE most_recent=1 and repo_path="%s")''' % (repo_path, repo_path))

  cursor.execute('''UPDATE backups SET most_recent=0 WHERE most_recent=1 and repo_path="%s"''' % repo_path)
  cursor.execute('''INSERT INTO backups (repo_path, created_at, git_command, most_recent) VALUES (?, ?, ?, ?)''',
    (repo_path, created_at, git_command, 1))

  backupid = cursor.lastrowid
  backupdir = common_path + "backups/" + str(backupid)

  # first, clear the folder
  subprocess.call(["rm", "-rf", backupdir])

  # actually copy the backup
  subprocess.call(["cp", "-a", repo_path + "/.", backupdir])
  print "Git Undo: Backed up to " + backupdir

  sys.stdout.flush()

# returns commit id of the previous commit
def getLastCommit():
  counter = 2
  x = subprocess.check_output(["git", "log"])
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
  x = subprocess.check_output(["git", "log"])
  y = x.split('\n')
  for i in y:
    temp = i.split()
    if (temp[0]=="commit"):
      return temp[1]
  return False  

# returns curent branch
def getBranch():
  x = subprocess.check_output(["git", "branch"])
  y = x.split('\n')
  for i in y:
    if (i[:1]=="*"):
      return i[2:]
  return False



def undo():
  result = cursor.execute('''SELECT * FROM backups WHERE repo_path="%s" and most_recent=1''' % repo_path)
  row = result.fetchone()

  backupid = row[0]
  command_to_undo = row[3]
  current_timestamp = row[2]
  git_args = command_to_undo.split(" ")[1:]

  print "repo_path: " + repo_path

  if prompt(command_to_undo):
    if git_args[0] == "push":
      undoPush()
    else:
      restoreBackup(backupid)

    cursor.execute('''UPDATE backups SET most_recent=0 WHERE most_recent=1 and repo_path="%s"''' % repo_path)
    cursor.execute('''UPDATE backups SET most_recent=1 WHERE backupid = (SELECT backupid FROM backups WHERE created_at < %i and repo_path = "%s" ORDER BY created_at DESC LIMIT 1)''' % (current_timestamp, repo_path))

    conn.commit()
    conn.close()

  else: # user does not want to continue undo
    return

def redo():
  last = cursor.execute('''SELECT * FROM backups WHERE repo_path="%s" ORDER BY created_at DESC LIMIT 1''' % repo_path)
  
  most_recent_flag = last.fetchone()[4]

  ref_timestamp = row[2]
  
  # if the flag is currently at most recent repo path, then no path to redo
  if most_recent_flag==1:
    print "There are no more commands to redo."
  else:
    next_step = cursor.execute('''SELECT * FROM backups WHERE created_at > %i and repo_path = "%s" ORDER BY created_at ASC LIMIT 1''' % (ref_timestamp, repo_path))
    command_to_undo = next.step.fetchone()[3]
    git_args = command_to_undo.split(" ")[1:]

    # find next increment from current step, sets to 1
    cursor.execute('''UPDATE backups SET most_recent=0 WHERE most_recent=1 and repo_path = "%s"''' % repo_path)
    cursor.execute('''UPDATE backups SET most_recent=1 FROM (SELECT * FROM backups WHERE created_at > %i and repo_path = "%s" ORDER BY created_at ASC LIMIT 1)''' % (ref_timestamp, repo_path))

    # execute redo
    subprocess.call(git_args)

def restoreBackup(backupid):
  backupdir = common_path_escaped + "backups/" + str(backupid)

  # actually copy the backup
  # os.chdir("..")
  subprocess.call("rm -rf {,.[!.],..?}*;cp -r " + backupdir + "/ .", shell=True)

  # os.chdir(repo_path)

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

def prompt(command):
  print "Are you sure you want to undo the following command: \n\t%s " % command
  ans = raw_input('(y/n): ')
  if ans.lower()=="y" or ans.lower()=="yes":
    return True
  elif ans.lower()=="n" or ans.lower()=="no":
    print "Canceling undo."
    return False
  else:
    raise ValueError("Sorry bro I have no idea what you're saying.  Bye.")


# Main
try:
  setup()
  if sys.argv[1] == "undo":
    undo()
  else:
    if !(sys.argv[1] in ignore):
      backup()

    exit_code = subprocess.call(["git"] + sys.argv[1:])

    if exit_code !== 0:
      # undo the backup
      conn.rollback()
    else:
      conn.commit()
      
    conn.close()

except subprocess.CalledProcessError:
  pass
