import sys

from utils import *
import socket
import argparse
from tempfile import mkstemp
import shutil

parser = argparse.ArgumentParser(description='Bank Server')
parser.add_argument('-p', type=int, metavar='<Port>', help='The port to listen on', default=3000)
parser.add_argument('-s',metavar='<auth-file>', help='Name of the auth-file')
args = parser.parse_args()
# bank server
def server():
    if len(sys.argv) !=1:
        parser.print_help()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = args.p
    s.bind(('',port))
    s.listen()
    conn, addr= s.accept()
    with conn:
        print("Connection received from: ",addr)
        while True:
            data = conn.recv(1024)
            if data.decode('utf-8') == 'exit\n':
                conn.close()
                break
            print(data.decode('utf-8'))

def main() -> None:
    if is_admin():
        proper_exit('Error: the script must run as unprivileged/regular user')

    print("yo")



if __name__ == '__main__':
    try:
        server()
        #main()
    except Exception as err:
        print(err)
        proper_exit('Program encountered an error during execution and cannot continue. Contact the support team')