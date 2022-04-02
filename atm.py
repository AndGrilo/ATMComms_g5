import configparser
import sys

from utils import *
import socket
import argparse
import json
from tempfile import mkstemp
import shutil

# client atm


def run_atm(args):
    host = args.ip_address
    port = args.port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        #TO DO
        m = {"account": args.account, "auth_file": args.auth_file, "ip_address": args.ip_address, "port": args.port,
             "card_file": args.card_file, "balance": args.balance, "deposit_amount": args.deposit_amount,
             "withdraw_amount": args.withdraw_amount, "get": args.get}
        data = json.dumps(m)

        s.sendall(bytes(data,encoding="utf-8"))
        data = s.recv(1024)

        print(f"Received {data!r}")


def validate_args(args) -> Response:
    #  if len(args.filename) > 1 | len(args.port) > 1:
    #     return Response(False, 'Arguments cannot be duplicate')

    if not args.account:
        return Response(False, 'argument -a must be provided')

    if not args.balance and not args.deposit_amount and not args.withdraw_amount and not args.get:
        return Response(False, 'a mode of operations must be provided (-n | -d | -w | -g)')

    print(args)
    return Response(True, args)


def create_parser() -> argparse.ArgumentParser:
    description = 'ATM Client'
    usage = '-a <account> [-s <auth-file>] [-i <ip-address>] [-p <port>] [-c <card-file>] (-n <balance> | -d <amount> | -w <amount> | -g)'
    parser = argparse.ArgumentParser(usage=usage, description=description, exit_on_error=False)
    commands = parser.add_argument_group('available commands')

    commands.add_argument('-a', metavar='account', type=str, dest='account', help='Name of the account')
    commands.add_argument('-s', metavar='auth_file', type=str, dest='auth_file', help='Name of the auth-file')
    commands.add_argument('-i', metavar='ip_address', type=str, dest='ip_address', help='IP address to connect to', default='127.0.0.1')
    commands.add_argument('-p', metavar='port', type=int, dest='port', help='The port the bank is listening on', default=3000)
    commands.add_argument('-c', metavar='card_file', type=path_type, dest='card_file', help='The customer card file')

    mode = commands.add_mutually_exclusive_group()
    mode.add_argument('-n', metavar='balance', type=int, dest='balance', help='Create a new account with given balance')
    mode.add_argument('-d', metavar='deposit_amount', type=int, dest='deposit_amount', help='Amount to deposit')
    mode.add_argument('-w', metavar='withdraw_amount', type=int, dest='withdraw_amount', help='Amount to withdraw')
    mode.add_argument('-g', action='store_const', const='get', dest='get', help='Get balance')

    return parser


def main() -> None:
    #if is_admin():
        #proper_exit('Error: the script must run as unprivileged/regular user')

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
