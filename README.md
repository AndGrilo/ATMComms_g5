# g05-atm-communications

This is a suite of tools used to create and interact with bank accounts. It is composed of 2 tools:

- `bank.py` (The central bank server)
- `atm.py` (The client which will handle users inputs)

## Installation
**Important:** We use `python` and `pip` in this README. Use the correct executable according to your system, it may be `python3` or `python3.9` for Python, and `pip3` or `pip3.9` for pip).

**Our scripts are compatible with python 3.9 and above**

1. Download Python 3.9.7 [here](https://www.python.org/downloads/release/python-397/) (Can be the 32-bit or 64-bit version)
2. Execute the installer
3. **If installing Python on Windows:** install in user-mode, not as administrator  
   3.1. Un-check the option "Install launcher for all users" and click "Customize installation"  
   3.2. Un-check the option "Install for all users" and click "Install"
4. Open the shell and go to the script path
5. Verify if you are running Python 3.9.7 by executing in the shell: `python3 --version`
6. Verify if you are running pip for Python 3.9.x by executing in the shell: `pip3 --version`
7. Execute in the shell: `pip install pycryptodome`
8. Installation is done  

## Usage
- **python3 bank.py** `[-p <port>] [-s <auth-file>]`
- **python3 atm.py** `-a <account> [-s <auth-file>] [-i <ip-address>] [-p <port>] [-c <card-file>] (-n <balance> | -d <amount> | -w <amount> | -g)`

