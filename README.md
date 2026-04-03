# Test scripts for Entropy-based Compaction

## Prerequisites

### Find a workspace

For example, if you want to place all the stuff of this project in the home directory:

```shell
workspace=~
```

If you prefer to put everything in a subdirectory:

```shell
mkdir ~/EntropyCompaction
workspace=~/EntropyCompaction
```

### Clone this repo

```shell
cd $workspace
git clone <URL-to-this-repo> tests
cd tests
cd setup
```

### `./apt.sh`

### `./pip.sh`

For some Linux distros, a virtual environment for python3 is mandatory for pip3 to work, and you may encounter this error message:

```txt
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.
    
    If you wish to install a non-Debian-packaged Python package,
    create a virtual environment using python3 -m venv path/to/venv.
    Then use path/to/venv/bin/python and path/to/venv/bin/pip. Make
    sure you have python3-full installed.
    
    If you wish to install a non-Debian packaged Python application,
    it may be easiest to use pipx install xyz, which will manage a
    virtual environment for you. Make sure you have pipx installed.
    
    See /usr/share/doc/python3.11/README.venv for more information.

note: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.
hint: See PEP 668 for the detailed specification.
```

If you don't have a virtual environment yet, we provide a simple way to install one:

```shell
python3 -m venv ~/.venvs/base
echo ". ~/.venvs/base/bin/activate" >> ~/.profile
. ~/.profile
```

Then `pip.sh` should work fine.

### `./setup.sh`

Data and figures will be stored in `$workspace/data`.

## Generate figures

```shell
cd $workspace/data
$workspace/tests/plot/simulation.py
```
