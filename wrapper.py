import subprocess, sys

subprocess.call(["git"] + sys.argv[1:])