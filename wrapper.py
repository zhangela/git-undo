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
  global git_undo_on

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

  # Create table
  cursor.execute('''CREATE TABLE IF NOT EXISTS backups
    (backupid integer primary key autoincrement, repo_path text, created_at timestamp, git_command text, most_recent integer)''')

  cursor.execute('''CREATE TABLE IF NOT EXISTS git_undo_switch (git_undo_is_on integer)''')
  git_undo_switch = cursor.execute('''SELECT git_undo_is_on FROM git_undo_switch LIMIT 1''')

  print git_undo_switch.fetchone() 
  if git_undo_switch.fetchone() is None or git_undo_switch.fetchone()[0] == 1:
    git_undo_on = True
  else:
    git_undo_on = False

def backup_folder_from_backupid(backupid):
  backupid = cursor.lastrowid
  backupdir = common_path + "backups/" + str(backupid)

  return backupdir

def delete_directory(path):
  subprocess.call(["rm", "-rf", path])

def copy_directory(from_path, to_path):
  subprocess.call(["cp", "-a", from_path + "/.", to_path])

def backup():
  created_at = int(time.time() * 1000)
  git_command = "git " + " ".join(sys.argv[1:])

  # delete alternate undo timeline
  cursor.execute('''DELETE FROM backups WHERE
    repo_path="%s" and created_at >
    (SELECT created_at FROM backups WHERE most_recent=1 and repo_path="%s")''' % (repo_path, repo_path))

  # set all most recent flags to 0 and insert a new backup with most_recent = 1
  cursor.execute('''UPDATE backups SET most_recent=0 WHERE most_recent=1 and repo_path="%s"''' % repo_path)
  cursor.execute('''INSERT INTO backups (repo_path, created_at, git_command, most_recent) VALUES (?, ?, ?, ?)''',
    (repo_path, created_at, git_command, 1))

  backupdir = backup_folder_from_backupid(backupid)

  # first, clear the folder
  delete_directory(backupdir)

  # actually copy the backup
  copy_directory(repo_path, backupdir)

  # print message
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

def move_most_recent_flag_back():
  # move the most recent flag one step back
  cursor.execute('''UPDATE backups SET most_recent=0 WHERE most_recent=1 and repo_path="%s"''' % repo_path)
  cursor.execute('''UPDATE backups SET most_recent=1 WHERE backupid = (SELECT backupid FROM backups WHERE created_at < %i and repo_path = "%s" ORDER BY created_at DESC LIMIT 1)''' % (current_timestamp, repo_path))
  conn.commit()

def undo_with_backup():
  backup()
  undo()
  undo()

def undo():
  # where we are
  result = cursor.execute('''SELECT * FROM backups WHERE repo_path="%s" and most_recent=1''' % repo_path)
  row = result.fetchone()

  if row is None:
    print "There are no more actions to undo."
    return

  backupid = row[0]
  command_to_undo = row[3]
  current_timestamp = row[2]
  git_args = command_to_undo.split(" ")[1:]

  print "repo_path: " + repo_path

  if prompt("undo", command_to_undo):
    if git_args[0] == "push":
      undoPush()
    else:
      restoreBackup(backupid)

    move_most_recent_flag_back()

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

  # a hacky command that Angela found on the internet
  subprocess.call("rm -rf {,.[!.],..?}*;cp -r " + backupdir + "/ .", shell=True)

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

def prompt(task, action):
  print "Are you sure you want to "+task+" the following action: \n\t%s " % action
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
  if sys.argv[1] == "undo" and sys.argv[2] == "on":
    print "Git Undo is now on. \nType 'git undo' to undo up to 5 recent git commands."
    git_undo_on = True
    cursor.execute('''UPDATE git_undo_switch SET git_undo_is_on = 1''')
  elif sys.argv[1] == "undo" and sys.argv[2] == "off":
    print "Git Undo is now off. \nYou won't be able to undo git actions!"
    git_undo_on = False
    cursor.execute('''UPDATE git_undo_switch SET git_undo_is_on = 0''')
  elif (sys.argv[1] == "undo" or sys.argv[1] == "redo") and (not git_undo_on):
      print "Git Undo is currently off. \n Type 'git undo on' to turn on Git Undo."
  
  elif sys.argv[1] == "undo":
    result = cursor.execute('''SELECT * FROM backups WHERE repo_path="%s" ORDER BY created_at DESC LIMIT 1''' % repo_path)
    row = result.fetchone()
    most_recent_flag = row[4]

    if most_recent_flag==1:
      undo_with_backup()
    else:
      undo()
  
  elif sys.argv[1] == "redo":
    redo()
    conn.commit()
  
  else:

    if git_undo_on: ## Git Undo is On
      if sys.argv[1] not in ignore:
        backup()
      exit_code = subprocess.call(["git"] + sys.argv[1:])

      if exit_code != 0:
        # undo the backup
        conn.rollback()
      else:
        conn.commit()
      conn.close()

    else: ## Git Undo is Off
      subprocess.call(["git"] + sys.argv[1:])

except subprocess.CalledProcessError:
  pass
