import configparser
import sys

from utils import *
import socket
import argparse
import json
import signal
from decimal import *
from tempfile import mkstemp
import shutil

# bank server
users = {}


def new_account(data) -> Response:
    if float(data["create"]["initial_balance"]) < 10.00:
        #return Response(False, 'minimum initial balance must be 10')
        return Response(False, '255')

    if data["create"]["account"] in users:
        #return Response(False, 'account already exists')
        return Response(False, '255')

    resp = {"account":data["create"]["account"],"initial_balance":data["create"]["initial_balance"],"balance":data["create"]["initial_balance"]}
    #    users = {
    #        data["create"]["account"]: resp
    #    }
    users.update({data["create"]["account"]: resp})

    return Response(True, json.dumps(resp))


def deposit(data) -> Response:
    if float(data["deposit"]["deposit"]) <= 0.00:
        #return Response(False, 'invalid amount to deposit')
        return Response(False, '255')

    if data["deposit"]["account"] in users:
        users[data["deposit"]["account"]]["balance"] += float(data["deposit"]["deposit"])
        resp = {"account": data["deposit"]["account"], "deposit": data["deposit"]["deposit"]}
        return Response(True, json.dumps(resp))
    else:
        #return Response(False, 'account does not exist')
        return Response(False, '255')


def withdraw(data) -> Response:
    if float(data["withdraw"]["withdraw"]) <= 0.00:
        #return Response(False, 'invalid amount to withdraw')
        return Response(False, '255')

    if data["withdraw"]["account"] in users:
        if (users[data["withdraw"]["account"]]["balance"] - data["withdraw"]["withdraw"]) < 0.00:
            #return Response(False, 'not enough balance to withdraw that amount')
            return Response(False, '255')

        users[data["withdraw"]["account"]]["balance"] -= float(data["withdraw"]["withdraw"])
        resp = {"account": data["withdraw"]["account"], "withdraw": data["withdraw"]["withdraw"]}
        return Response(True, json.dumps(resp))
    else:
        #return Response(False, 'account does not exist')
        return Response(False, '255')


def get_balance(data) -> Response:
    if data["get"]["account"] in users:
        resp = {"account": data["get"]["account"], "balance": users[data["get"]["account"]]["balance"]}
        return Response(True, json.dumps(resp))
    else:
        #return Response(False, 'account does not exist')
        return Response(False, '255')


def run_server(args):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as err:
        print("socket creation failed with error %s" % err)

    port = args.port

    s.bind(('', port))
    s.listen()
    print("listening on port ", port)

    try:
        while True:
            conn, addr = s.accept()
            data = conn.recv(1024)

            json_resp = json.loads(data.decode('utf-8'))  # convert str to json

            if len(data.decode('utf-8')) <= 0 :
                conn.close()
                continue

            if "create" in json_resp:
                response = new_account(json_resp)
                if response.success:
                    print(response.result)
                    conn.send(bytes(response.result, encoding='utf-8'))
                else:
                    conn.send(bytes(response.result, encoding='utf-8'))

                conn.close()
                continue

            if "deposit" in json_resp:
                response = deposit(json_resp)
                if response.success:
                    print(response.result)
                    conn.send(bytes(response.result, encoding='utf-8'))
                else:
                    conn.send(bytes(response.result, encoding='utf-8'))

                conn.close()
                continue

            if "withdraw" in json_resp:
                response = withdraw(json_resp)
                if response.success:
                    print(response.result)
                    conn.send(bytes(response.result, encoding='utf-8'))
                else:
                    conn.send(bytes(response.result, encoding='utf-8'))

                conn.close()
                continue

            if 'get' in json_resp:
                response = get_balance(json_resp)
                if response.success:
                    print(response.result)
                    conn.send(bytes(response.result, encoding='utf-8'))
                else:
                    conn.send(bytes(response.result, encoding='utf-8'))

                conn.close()
                continue

    except KeyboardInterrupt:
        proper_exit('SIGTERM')


def create_auth_file(filename: str):
    try:
        f = open(filename, "x")
        f.write(filename)
        f.close()
        print("created")
    except Exception:
        proper_exit('File exists')


def validate_args(args) -> Response:
    #  if len(args.filename) > 1 | len(args.port) > 1:
    #     return Response(False, 'Arguments cannot be duplicate')
    return Response(True, args)


def create_parser() -> argparse.ArgumentParser:
    description = 'Bank Server'
    usage = '[-p <port>] [-s <auth-file>]'
    parser = argparse.ArgumentParser(usage=usage, description=description, exit_on_error=False)

    parser.add_argument('-p', type=int, metavar='<port>', dest='port', help='The port to listen on', default=3000)
    parser.add_argument('-s', type=str, metavar='<auth_file>', dest='filename', help='Name of the auth-file',
                        default='bank.auth')

    return parser


def main() -> None:
    # if is_admin():
    # proper_exit('Error: the script must run as unprivileged/regular user')

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


def __init__(self):
    signal.signal(signal.SIGTERM, proper_exit('SIGTERM'))


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(err)
        proper_exit('Program encountered an error during execution and cannot continue. Contact the support team')
