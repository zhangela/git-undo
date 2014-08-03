import subprocess
import os
import sys

prompt = '> '

common_path = os.path.expanduser("~/Library/Application Support/git-undo/")

if not os.path.isdir(common_path):
  os.mkdir(common_path)

def getLastCommit():
	counter = 2
	x = subprocess.check_output(["git"]+["log"])
	y = x.split('\n')
	for i in y:
		temp = i.split()
		if temp==[]:
			continue
		elif (i.split()[0]=="commit"):
			counter-=1

		if counter==0:
			return i.split()[1]
	return False	

def getBranch():
	x = subprocess.check_output(["git"]+["branch"])
	y = x.split('\n')
	for i in y:
		if (i[:1]=="*"):
			return i[2:]
	return False

def undoPush():
	# if system.denyNonFastForwards and denyDeletes:
	if False:
		print("")
	# elif system.denyNonFastForwards and master is not the only branch
	elif False:
		print("")
	# elif system.denyNonFastForwards
	elif False:
		print("sorry we don't support you yet.")
	# else
	else:
		print("hi")
		print(["git","push","-f","origin",getLastCommit(),":",getBranch()])
 		subprocess.call(["git","push","-f","origin",getLastCommit()+":"+getBranch()])

## Main Code
print (sys.argv[1])

if (sys.argv[1] == "push"):
	undoPush()
if (sys.argv[1] == "test"):
	print("tester")
else:
	subprocess.call(["git"] + sys.argv[1:])


## Code for prompts

# print("Your repository has a denyNonFastForward flag on, so the history \
# 	cannot be overwritten. The undo-push will be written into the git history.\
# 	 Is that alright? (Y/N)")
# ans = raw_input(prompt)
# if (ans.lower()=="y" or ans.lower()=="yes"):
# elif (ans.lower()=="n" or ans.lower()=="no"):
# else:
# 	raise ValueError("Sorry bro I have no idea what you're saying.  Bye.")