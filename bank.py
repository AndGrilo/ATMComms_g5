import configparser
import sys

from utils import *
import socket
import argparse
import json
import signal
import os,binascii
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


def get_card_file_name(data):
    if "create" in data:
        card_file_name = data["create"]["card_file"]
    elif "withdraw" in data:
        card_file_name = data["withdraw"]["card_file"]
    elif "deposit" in data:
        card_file_name = data["deposit"]["card_file"]
    elif "get" in data:
        card_file_name = data["get"]["card_file"]
    return card_file_name


def run_server(args):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as err:
        print("socket creation failed with error %s" % err)

    port = args.port

    try:
        s.bind(('', port))
        s.listen()

        try:
            while True:
                conn, addr = s.accept()
                print("connected with client")

                encrypted_command_request = conn.recv(1024)
                print(encrypted_command_request.decode())

                content = open(args.filename, "r").read()

                if len(encrypted_command_request.decode('utf-8')) <= 0:
                    conn.close()
                    continue

                denc_json = decrypt(key=content, data=encrypted_command_request.decode())
                json_resp = json.loads(denc_json.decode('utf-8'))  # convert str to json
                print(json_resp)

                challenge = generate_random_string(16)
                conn.send(bytes(challenge, encoding='utf-8'))
                print("sent challenge "+challenge)

                challenge_response = conn.recv(1024)
                print("received chal response "+challenge_response.decode())

                card_file_name = get_card_file_name(json_resp)
                print("a card file chama-se " + card_file_name)
                card_file_content = open(card_file_name, "r").read()

                challenge_response_solution = decrypt(key=card_file_content, data=challenge_response.decode())
                print("chal response solution "+challenge_response_solution.decode())

                if challenge_response_solution.decode() == challenge:
                    print("client authenticated, challenge matches")

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
                else:
                    conn.send(bytes("255", encoding='utf-8'))
                    conn.close()
                    #s.close()
                    print("client NOT authenticated, challenge differ")


                conn.close()
                continue
        except KeyboardInterrupt:
            s.close()
            conn.close()
            proper_exit('SIGTERM', 255)
    except Exception as err:
        print(err)
        s.close()
        proper_exit("protocol error", 63)


def create_auth_file(filename: str):
    try:
        f = open(filename, "x")
        #f.write("xxxxyyyyxxxxyyyy")
        content = generate_random_string(16)
        f.write(content)
        print("wrote "+content)
        f.close()
        print("created")
    except Exception:
        proper_exit('File exists')


def validate_args(args) -> Response:
    #  if len(args.filename) > 1 | len(args.port) > 1:
    #     return Response(False, 'Arguments cannot be duplicate')
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
    description = 'Bank Server'
    usage = '[-p <port>] [-s <auth-file>]'
    parser = argparse.ArgumentParser(usage=usage, description=description, exit_on_error=False)

    parser.add_argument('-p', type=int, metavar='<port>', dest='port', help='The port to listen on', default=3000)
    parser.add_argument('-s', type=str, metavar='<filename>', dest='filename', help='Name of the auth-file',
                        default='bank.auth')

    return parser


def main() -> None:
    # if is_admin():
    # proper_exit('Error: the script must run as unprivileged/regular user')

    parser = create_parser()

    try:
        args = parser.parse_args()
        if check_double_params(sys.argv):
            exit(255)
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
    signal.signal(signal.SIGTERM, proper_exit('SIGTERM', 255))


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(err)
        proper_exit('Program encountered an error during execution and cannot continue')
