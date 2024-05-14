# REQUIREMENTS

The following should be installed by apt, yum, etc., depending on your OS.

 * Python 3.8 to 3.12
 * librsync v0.9.6 or later
 * GnuPG for encryption
 * intltool for installing translations
 
If you install from source you will also need:

* pipx v1.4.3 or later for installation (available via pip)
* Python development files, normally found in module 'python3-dev'.
* librsync development files, normally found in module 'librsync-dev'.

# INSTALLATION

Since Python3.11 site package directories have been marked as **Externally Managed** and now require 
using `--break-system-packages` to install into them.  This means that a package like duplicity with
many includes must use a virtual environment, or venv, to install their packages.  Rather than going
through the manual process of producing a venv, activating it, installing duplicity, etc., we will be
using `pipx` from now on to install duplicity.  This way we get the same effect as a pip install, but
now isolated in a venv.

To install follow instructions below.  Steps (1) and (2) are important.

## (1) Update packaging to current version
PyPA (Python Packaging Authority) has been making rapid changes to the way
we install Python modules.  To accomodate installing new packages on older
systems, it is necessary to upgrade packaging tools like this:
```shell
sudo pip install pipx
````
a**NOTE: _Failure to update will probably result in a failed install._  <--IMPORTANT!**  

To make sure the pipx dirs are on your path do:
```shell
sudo pipx --global ensurepath  # for all users
pipx ensurepath                # for single user
```

## (2) Uninstall Previous Version
If you have an existing duplicity on your path and it was not
installed by setup.py, pip, or pipx, you must uninstall it
using the same method by which it was installed.

You can tell if you have multiple instances by doing
```shell
which -a duplicity
```
and then use apt, yum, snap, or other command to remove them.

## (3) Install Using Pipx
Chose one of the following depending on whether you want to install for 
all users or the current user.  Use both if needed.  

With `--global` duplicity will be installed in `/usr/local/bin/duplicity` 
and its many packages in `/opt/pipx/venvs/duplicity`.

Without `--global` duplicity will be installed in `~/.local/bin/duplicity` 
and its many packages in `~/.local/pipx/venvs/duplicity`.

### (3a) Normal Install

#### From Pipx (all users)
```shell
sudo pipx --global install duplicity[==version]
```

#### From Pipx (single user)
```shell
pipx install duplicity[==version]
```

### (3b) Suffixed Install
You can keep multiple versions of duplicity by supplying `--suffix=version`.

#### From Pipx (all users)
```shell
sudo pipx --global install --suffix=version duplicity[==version]
```

#### From Pipx (single user)
```shell
pipx install --suffix=version duplicity[==version]
```

# DEVELOPMENT

For more information on downloading duplicity's source code from the
code repository and developing for duplicity, see README-REPO.

For source docs: http://duplicity.readthedocs.io/

# HELP

For more information see the duplicity web site at:

  http://duplicity.us

  or at:

  http://duplicity.gitlab.io

or post to the mailing list at:

  https://lists.nongnu.org/mailman/listinfo/duplicity-talk

or post a new issue at:

  https://gitlab.com/duplicity/duplicity/-/issues
