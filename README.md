Git Undo
========

A wrapper around `git` that lets you undo unfortunate git commands by making backups of your git repository. Currently, you can undo the 5 most recent git commands.

Installation
----

1. Download wrapper.py into any directory of your choice.
2. `cd` into that directory and type `alias git="python $(pwd)/wrapper.py"`
3. Backups and configuration files are stored in `~/.git-undo/`

## Usage

1. If you make a mistake with a `git` command, type `git undo` and things will return to the state they were in before that command was executed.
2. You can also redo an action with `git redo`.
4. If you want to turn off Git Undo, type `git undo off`; To turn it back on, type `git undo on`

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

## Future Features

1. Per-repository configuration
2. More efficient backups