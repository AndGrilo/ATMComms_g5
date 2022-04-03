import configparser
import sys

from utils import *
import socket
import argparse
import json
from decimal import *
from tempfile import mkstemp
import shutil


# bank server
users = {}

def validate_args(args) -> Response:
    #  if len(args.filename) > 1 | len(args.port) > 1:
    #     return Response(False, 'Arguments cannot be duplicate')
    print(args)
    return Response(True, args)


def create_parser() -> argparse.ArgumentParser:
    description = 'Bank Server'
    usage = '[-p <port>] [-s <auth-file>]'
    parser = argparse.ArgumentParser(usage=usage, description=description, exit_on_error=False)

    parser.add_argument('-p', type=int, metavar='<port>', dest='port', help='The port to listen on', default=3000)
    parser.add_argument('-s', type=str, metavar='<auth_file>', dest='filename', help='Name of the auth-file',
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

    #conn, addr = s.accept()
    #with conn:
        #print("Connection received from: ", addr)
    while True:
        #print("olá")
        conn, addr = s.accept()
        data = conn.recv(1024)
        if data.decode('utf-8') == 'exit\n':
            conn.close()
            break
        if len(data.decode('utf-8')) <= 0 :
            conn.close()
            continue

        json_resp = json.loads(data.decode('utf-8')) # convert str to json
        if "create" in json_resp:
            success = new_account(json_resp)
            conn.send(bytes(success,encoding='utf-8'))
            print(success)
            #print(users)
            conn.close()
            continue
        if "deposit" in json_resp:
            success = deposit(json_resp)
            conn.send(bytes(success,encoding='utf-8'))
            print(success)
            #print(users)
            conn.close()
            continue
        if "withdraw" in json_resp:
            success = withdraw(json_resp)
            conn.send(bytes(success,encoding='utf-8'))
            print(success)
            #print(users)
            conn.close()
            continue
        if 'get' in json_resp:
            success = get_balance(json_resp)
            conn.send(bytes(success,encoding='utf-8'))
            print(success)
            #print(users)
            conn.close()
            continue



def new_account(data):
    if float(data["create"]["initial_balance"]) < 10.00 or data["create"]["account"] in users:
        proper_exit()
    resp =  {"account":data["create"]["account"],"initial_balance":data["create"]["initial_balance"],"balance":data["create"]["initial_balance"]}
#    users = {
#        data["create"]["account"]: resp
#    }
    users.update({data["create"]["account"]: resp})
    return json.dumps(resp)

def deposit(data):
    if float(data["deposit"]["deposit"]) <= 0.00:
        proper_exit()
    if data["deposit"]["account"] in users:
        users[data["deposit"]["account"]]["balance"] += float(data["deposit"]["deposit"])
        resp = {"account":data["deposit"]["account"],"deposit":data["deposit"]["deposit"]}
        return json.dumps(resp)
    else:
        proper_exit()

def withdraw(data):
    if float(data["withdraw"]["withdraw"]) <= 0.00 or (users[data["withdraw"]["account"]]["balance"]-data["withdraw"]["withdraw"]) < 0.00:
        proper_exit()
    if data["withdraw"]["account"] in users:
        users[data["withdraw"]["account"]]["balance"] -= float(data["withdraw"]["withdraw"])
        resp = {"account":data["withdraw"]["account"],"withdraw":data["withdraw"]["withdraw"]}
        return json.dumps(resp)
    else:
        proper_exit()

def get_balance(data):
    if data["get"]["account"] in users:
        resp = {"account":data["get"]["account"],"balance":users[data["get"]["account"]]["balance"]}
        return json.dumps(resp)
    else:
        proper_exit()



def create_auth_file(filename: str):
    try:
        f = open(filename, "x")
        f.write(filename)
        f.close()
        print("created")
    except Exception:
        proper_exit('File exists')


def main() -> None:
    #if is_admin():
        #proper_exit('Error: the script must run as unprivileged/regular user')

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
