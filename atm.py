import configparser
import sys

from utils import *
import socket
import argparse
import json
import hmac
import hashlib
import string
import random
from tempfile import mkstemp
import shutil


# client atm
card = ""

def create_card_file(args) -> Response:
    key = generate_random_string(16)
    card = hmac.new(bytes(key, encoding='utf-8'), args.account.encode(), hashlib.sha256).hexdigest()

    if args.card_file:
        fname = args.card_file
    else:
        fname = args.account + ".card"
    try:
        f = open(fname, "x")
        f.write(args.account + ":" + card)
        f.close
    except Exception:
        return Response(False, 'card file exists')

    return Response(True, card)


def structure_command(args):
    if args.get:
        m = {
            "get": {"account": args.account, "auth_file": args.auth_file, "ip_address": args.ip_address,
                    "port": args.port,
                    "card_file": args.card_file, "get": args.get}
        }
    if args.deposit_amount:
        m = {
            "deposit": {"account": args.account, "auth_file": args.auth_file, "ip_address": args.ip_address,
                        "port": args.port,
                        "card_file": args.card_file, "deposit": args.deposit_amount}
        }
    if args.withdraw_amount:
        m = {
            "withdraw": {"account": args.account, "auth_file": args.auth_file, "ip_address": args.ip_address,
                         "port": args.port,
                         "card_file": args.card_file, "withdraw": args.withdraw_amount}
        }
    if args.balance:
        response = create_card_file(args)
        m = {
            "create": {"account": args.account, "auth_file": args.auth_file, "ip_address": args.ip_address,
                       "port": args.port,
                       "card_file": args.card_file, "initial_balance": args.balance,"card_hash":response.result}
        }


    return m


def run_atm(args):

    host = args.ip_address
    port = args.port

    m = structure_command(args)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            print("connected with server")

            data = json.dumps(m)
            print(type(data))

            content = open(args.auth_file, "r").read().rstrip()
            print("encrypting "+data+" with key "+content)
            encrypted_data = encrypt(key=content, data=bytes(data, encoding='utf-8'))

            print(encrypted_data)
            s.sendall(bytes(encrypted_data, encoding="utf-8"))

            challenge = s.recv(1024)
            print(challenge.decode())

            card_file_content = open(args.card_file, "r").read().rstrip()
            challenge_response = encrypt(key=card_file_content, data=challenge)

            s.sendall(bytes(challenge_response, encoding="utf-8"))

            data = s.recv(1024)
            if data.decode() == '255':
                exit(255)

            print(f"Received {data!r}")

    except Exception as err:
        print(err)
        exit(63)


def validate_args(args) -> Response:
    #  if len(args.filename) > 1 | len(args.port) > 1:
    #     return Response(False, 'Arguments cannot be duplicate')

    if not args.account:
        return Response(False, 'argument -a must be provided')

    if not args.balance and not args.deposit_amount and not args.withdraw_amount and not args.get:
        return Response(False, 'a mode of operations must be provided (-n | -d | -w | -g)')

    if not args.auth_file:
        args.auth_file = "bank.auth"

    if not args.card_file:
        args.card_file = args.account+".card"

    return Response(True, args)


def check_double_params(listOfElems):
    setOfElems = set()
    for elem in listOfElems:
        if elem in setOfElems:
            return True
        else:
            setOfElems.add(elem)
    return False


def create_parser() -> argparse.ArgumentParser:
    description = 'ATM Client'
    usage = '-a <account> [-s <auth-file>] [-i <ip-address>] [-p <port>] [-c <card-file>] (-n <balance> | -d <amount> | -w <amount> | -g)'
    parser = argparse.ArgumentParser(usage=usage, description=description, exit_on_error=False)
    commands = parser.add_argument_group('available commands')

    commands.add_argument('-a', metavar='account', type=str, dest='account', help='Name of the account')
    commands.add_argument('-s', metavar='auth_file', type=str, dest='auth_file', help='Name of the auth-file')
    commands.add_argument('-i', metavar='ip_address', type=str, dest='ip_address', help='IP address to connect to',
                          default='127.0.0.1')
    commands.add_argument('-p', metavar='port', type=int, dest='port', help='The port the bank is listening on',
                          default=3000)
    commands.add_argument('-c', metavar='card_file', type=str, dest='card_file', help='The customer card file')

    mode = commands.add_mutually_exclusive_group()
    mode.add_argument('-n', metavar='balance', type=float, dest='balance',
                      help='Create a new account with given balance')
    mode.add_argument('-d', metavar='deposit_amount', type=float, dest='deposit_amount', help='Amount to deposit')
    mode.add_argument('-w', metavar='withdraw_amount', type=float, dest='withdraw_amount', help='Amount to withdraw')
    mode.add_argument('-g', action='store_const', const='get', dest='get', help='Get balance')

    return parser


def main() -> None:
    # if is_admin():
    # proper_exit('Error: the script must run as unprivileged/regular user')

    parser = create_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        proper_exit('', 0)

    try:
        args = parser.parse_args()
        if check_double_params(sys.argv):
            exit(255)
        response = validate_args(args)
        if response.success:
            args = response.result
            run_atm(args)
        else:
            proper_exit('', 255)
    except argparse.ArgumentError as er:
        parser.error(str(er))


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(err)
        proper_exit('Program encountered an error during execution and cannot continue. Contact the support team')
