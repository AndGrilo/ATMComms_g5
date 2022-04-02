import configparser
import sys

from utils import *
import socket
import argparse
from tempfile import mkstemp
import shutil

# client atm


def validate_args(args) -> Response:
    #  if len(args.filename) > 1 | len(args.port) > 1:
    #     return Response(False, 'Arguments cannot be duplicate')
    print(args)
    return Response(True, args)


def create_parser() -> argparse.ArgumentParser:
    description = 'ATM Client'
    usage = '-a <account> ...'
    parser = argparse.ArgumentParser(usage=usage, description=description, exit_on_error=False)



    return parser


def run_atm(args):
    host = args.ipaddress
    port = args.port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(b"Hello, world")
        data = s.recv(1024)

        print(f"Received {data!r}")


def main() -> None:
    if is_admin():
        proper_exit('Error: the script must run as unprivileged/regular user')

    parser = create_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        proper_exit('', 0)

    try:
        args = parser.parse_args()
        response = validate_args(args)
        if response.success:
            args = response.result
            run_atm(args)
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