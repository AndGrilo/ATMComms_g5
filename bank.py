import configparser
import sys

from utils import *
import socket
import argparse
from tempfile import mkstemp
import shutil


# bank server


def validate_args(args) -> Response:
    #  if len(args.filename) > 1 | len(args.port) > 1:
    #     return Response(False, 'Arguments cannot be duplicate')
    print(args)
    return Response(True, args)


def create_parser() -> argparse.ArgumentParser:
    description = 'Bank Server'
    usage = '[-p <port>] [-s <auth-file>]'
    parser = argparse.ArgumentParser(usage=usage, description=description, exit_on_error=False)

    parser.add_argument('-p', type=int, metavar='<Port>', dest='port', help='The port to listen on', default=3000)
    parser.add_argument('-s', type=str, metavar='<auth-file>', dest='filename', help='Name of the auth-file',
                        default='bank.auth')

    return parser


def run_server(args):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Socket successfully created")
    except socket.error as err:
        print("socket creation failed with error %s" % err)

    port = args.port

    s.bind(('', port))
    s.listen()
    print("listening on port ", port)

    conn, addr = s.accept()
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

    try:
        args = parser.parse_args()
        response = validate_args(args)
        if response.success:
            args = response.result
            create_auth_file(args.filename)
            run_server(args)
        else:
            proper_exit(response.result)
    except argparse.ArgumentError as er:
        parser.error(str(er))


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(err)
        proper_exit('Program encountered an error during execution and cannot continue. Contact the support team')
