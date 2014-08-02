import subprocess
import os
import sys

# folder to store all settings and backups
common_path = os.path.expanduser("~/Library/Application Support/git-undo/")

# make sure the settings and backups folder exists
if not os.path.isdir(common_path):
  os.mkdir(common_path)

subprocess.call(["git"] + sys.argv[1:])