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
  global ignore

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

def specialUndo():
  backup()
  undo()
  undo()

def undo():
  # where we are
  result = cursor.execute('''SELECT * FROM backups WHERE repo_path="%s" and most_recent=1''' % repo_path)
  row = result.fetchone()

  if row is None:
    print "There are no more commands to undo."
    return
  backupid = row[0]
  command_to_undo = row[3]
  current_timestamp = row[2]
  git_args = command_to_undo.split(" ")[1:]

  print "repo_path: " + repo_path

  if prompt("undo",command_to_undo):
    if git_args[0] == "push":
      undoPush()
    else:
      restoreBackup(backupid)

    cursor.execute('''UPDATE backups SET most_recent=0 WHERE most_recent=1 and repo_path="%s"''' % repo_path)
    cursor.execute('''UPDATE backups SET most_recent=1 WHERE backupid = (SELECT backupid FROM backups WHERE created_at < %i and repo_path = "%s" ORDER BY created_at DESC LIMIT 1)''' % (current_timestamp, repo_path))

    conn.commit()

  else: # user does not want to continue undo
    return

def redo():
  current = cursor.execute('''SELECT * FROM backups WHERE repo_path = "%s" and most_recent=1''' % repo_path)
  current_backupid = current.fetchone()[0]
  last = cursor.execute('''SELECT * FROM backups WHERE repo_path="%s" and backupid>%i ORDER BY created_at ASC LIMIT 2''' % (repo_path,current_backupid))

  result = last.fetchall()
  # if list size is not 2, then we're screwed.
  #there is nothing to redo.

  #if list size is 2, then we good. 
  
  # if the flag is currently at most recent repo path, then no path to redo
  if len(result)<2:
    print "There are no more commands to redo."
  else:
    # result[0] is 1 steps later
    # result[1] is 2 steps later
    onestep = result[0]
    twostep = result[1]

    command_to_redo = onestep[3]
    git_args = command_to_redo.split(" ")[1:]

    #reset backup to be twostep's backupdata. 
    onestepid = onestep[0]
    nextbackupid = twostep[0]

    if prompt("redo",command_to_redo):
      if git_args[0] == "push":
        print "push redo"
        subprocess.call(command_to_redo)
      else:
        print "rebacked"
        restoreBackup(nextbackupid)
      # set onestep's recent to be 1 
      cursor.execute('''UPDATE backups SET most_recent=0 WHERE most_recent=1 and repo_path = "%s"''' % repo_path)
      cursor.execute('''UPDATE backups SET most_recent=1 WHERE backupid=%i''' % onestepid)

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

def prompt(task, command):
  print "Are you sure you want to "+task+" the following command: \n\t%s " % command
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

    result = cursor.execute('''SELECT * FROM backups WHERE repo_path="%s" ORDER BY created_at DESC LIMIT 1''' % repo_path)
    row = result.fetchone()
    most_recent_flag = row[4]

    if most_recent_flag==1:
      specialUndo()
    else:
      undo()
  elif sys.argv[1] == "redo":
    redo()
  else:
    if sys.argv[1] not in ignore:
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
