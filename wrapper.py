import subprocess
import os
import sys

common_path = os.path.expanduser("~/Library/Application Support/git-undo/")

if not os.path.isdir(common_path):
  os.mkdir(common_path)

subprocess.call(["git"] + sys.argv[1:])