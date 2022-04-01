import sys

from utils import *
import socket
import argparse
from tempfile import mkstemp
import shutil

# bank server


def create_parser() -> argparse.ArgumentParser:
    description = 'Bank Server'
    usage = '-p <port> -s <auth-file>'
    parser = argparse.ArgumentParser(usage=usage, description=description, exit_on_error=False)

    parser.add_argument('-p', type=int, metavar='<Port>', dest='port', help='The port to listen on', default=3000)
    parser.add_argument('-s', type=str, metavar='<auth-file>', dest='filename', help='Name of the auth-file')

    return parser


def server(args):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = args.port
    s.bind(('', port))
    s.listen()
    print("listening on port ", port)
    conn, addr= s.accept()
    with conn:
        print("Connection received from: ", addr)
        while True:
            data = conn.recv(1024)
            if data.decode('utf-8') == 'exit\n':
                conn.close()
                break
            print(data.decode('utf-8'))


def create_auth_file(filename: str):
    try:
        f = open(filename, "x")
        f.write(filename)
        f.close()
        print("created")
    except Exception:
        proper_exit('File exists')


def main() -> None:
    if is_admin():
        proper_exit('Error: the script must run as unprivileged/regular user')

    parser = create_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        proper_exit('', 0)

    args = parser.parse_args()
    create_auth_file(args.filename)
    server(args)


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(err)
        proper_exit('Program encountered an error during execution and cannot continue. Contact the support team')