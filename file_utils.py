import subprocess

def delete_directory(path):
  subprocess.call(["rm", "-rf", path])

def copy_directory(from_path, to_path):
  subprocess.call(["cp", "-a", from_path + "/.", to_path])