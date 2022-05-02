from utils import *
import socket
import argparse
import json
import time
import re
import hmac
import hashlib

TIMEOUT = 10
client_disconnected = False


def trade_messages(server_connection, client_connection):
    i = 0
    while i < 10:
        i+=1
        received_from_client = client_connection.recv(1024)
        print("received from client " + received_from_client.decode())

        server_connection.send(bytes(received_from_client.decode(), encoding='utf-8'))
        print("sent to server " + received_from_client.decode())

        received_from_server = server_connection.recv(1024)
        print("received from server " + received_from_server.decode())

        client_connection.send(bytes(received_from_server.decode(), encoding='utf-8'))
        print("sent to client " + received_from_client.decode())


def connect_to_server(args, client_connection):
    host = args.server_ip_address
    s_port = args.server_port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, s_port))
        print("connected with victim server")

        trade_messages(s, client_connection)


def run_mitm(args):
    active_connection = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    except socket.error as err:
        # print("socket creation failed with error %s" % err)
        print("protocol_error")
        exit(63)

    port = args.port

    try:
        s.bind(('', port))
        s.listen()

        try:
            while True:
                conn, addr = s.accept()
                conn.settimeout(TIMEOUT)
                print("connected with client victim")
                active_atm_connection = True

                connect_to_server(args, conn)

                conn.close()
                continue

        except KeyboardInterrupt:
            s.close()
            if active_connection:
                conn.close()
            exit(0)
    except Exception:
        s.close()
        if active_connection:
            conn.close()
        exit(255)


def validate_args(args) -> Response:
    #  if len(args.filename) > 1 | len(args.port) > 1:
    #     return Response(False, 'Arguments cannot be duplicate')
    return Response(True, args)


def create_parser() -> argparse.ArgumentParser:
    description = 'MITM program'
    usage = '[-p <port>] [-s <server-ip-address>] [-q <server-port>]'
    parser = argparse.ArgumentParser(usage=usage, description=description, exit_on_error=False)
    commands = parser.add_argument_group('available commands')

    commands.add_argument('-p', metavar='port', type=int, dest='port', help='The port the MITM should listen on to intercept comms',
                          default=4000)
    commands.add_argument('-s', metavar='server_ip_address', type=str, dest='server_ip_address', help='IP address the bank is running on',
                          default='127.0.0.1')
    commands.add_argument('-q', metavar='server_port', type=int, dest='server_port', help='The TCP port the bank is running on',
                          default=3000)

    return parser


def main() -> None:
    parser = create_parser()

    try:
        args = parser.parse_args()
        response = validate_args(args)
        if response.success:
            args = response.result

            run_mitm(args)

        else:
            exit(255)
    except argparse.ArgumentError as er:
        parser.error(str(er))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
    except Exception as err:
        print(err)
        exit(255)
