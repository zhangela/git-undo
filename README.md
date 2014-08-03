Git Undo
========

A wrapper around `git` that lets you undo unfortunate git commands by making backups of your git repository. Currently, you can undo the 5 most recent git commands.

Installation
----

1. Download wrapper.py into any directory of your choice.
2. `cd` into that directory and type `alias git2="python $(pwd)/wrapper.py"`
3. Use `git2` instead of `git` for all the normal git cases
4. If you make a mistake with a `git2` command, type `git2 undo` and voila!

### Commands you can't undo

Since these commands only show information and don't affect the state of the repository, we don't save them to the undo history.

+ git blame
+ git config
+ git describe
+ git diff
+ git log
+ git shortlog
+ git show
+ git status