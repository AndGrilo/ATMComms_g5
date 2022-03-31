from utils import *
from tempfile import mkstemp
import shutil

def main() -> None:
    if is_admin():
        proper_exit('Error: the script must run as unprivileged/regular user')

    print("yo")



if __name__ == '__main__':
    try:
        main()
    except Exception:
        proper_exit('Program encountered an error during execution and cannot continue. Contact the support team')