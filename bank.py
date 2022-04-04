from utils import *
import socket
import argparse
import json
import time

# bank server
users = {}
TIMEOUT = 10


def new_account(data) -> Response:
    if float(data["create"]["initial_balance"]) < 10.00:
        #return Response(False, 'minimum initial balance must be 10')
        return Response(False, '255')

    if data["create"]["account"] in users:
        #return Response(False, 'account already exists')
        return Response(False, '255')

    info = {"account":data["create"]["account"],"initial_balance":data["create"]["initial_balance"],"balance":data["create"]["initial_balance"],"card_hash":data["create"]["card_hash"],"card_file":data["create"]["card_file"]}
    resp = {"account":data["create"]["account"],"initial_balance":data["create"]["initial_balance"]}

    users.update({data["create"]["account"]: info})
    # print("User_info:", users)

    return Response(True, json.dumps(resp))


def deposit(data) -> Response:
    if float(data["deposit"]["deposit"]) <= 0.00:
        #return Response(False, 'invalid amount to deposit')
        return Response(False, '255')
    user_card = open(data["deposit"]["card_file"], "r").read()
    hash = user_card.split(":")
    if hash[1] != users[data["deposit"]["account"]]["card_hash"] or data["deposit"]["card_file"] != users[data["deposit"]["account"]]["card_file"]:
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
    user_card = open(data["withdraw"]["card_file"], "r").read()
    hash = user_card.split(":")
    if hash[1] != users[data["withdraw"]["account"]]["card_hash"] or data["withdraw"]["card_file"] != users[data["withdraw"]["account"]]["card_file"]:
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
    user_card = open(data["get"]["card_file"], "r").read()
    hash = user_card.split(":")
    if hash[1] != users[data["get"]["account"]]["card_hash"] or data["get"]["card_file"] != users[data["get"]["account"]]["card_file"]:
        return Response(False, '255')
    if data["get"]["account"] in users:
        resp = {"account": data["get"]["account"], "balance": users[data["get"]["account"]]["balance"]}
        return Response(True, json.dumps(resp))
    else:
        #return Response(False, 'account does not exist')
        return Response(False, '255')


def get_expire_date(data):
    if "create" in data:
        expire_date = data["create"]["expire_date"]
    elif "withdraw" in data:
        expire_date = data["withdraw"]["expire_date"]
    elif "deposit" in data:
        expire_date = data["deposit"]["expire_date"]
    elif "get" in data:
        expire_date = data["get"]["expire_date"]
    return expire_date


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
                # print("connected with client")
                active_connection = True

                try:
                    encrypted_command_request = conn.recv(1024)
                    # print(encrypted_command_request.decode())

                    try:
                        content = open(args.filename, "r").read()
                    except FileNotFoundError:
                        # print("bank authentication file does not exist")
                        conn.close()
                        continue

                    if len(encrypted_command_request.decode('utf-8')) <= 0:
                        conn.close()
                        continue

                    denc_json = decrypt(key=content, data=encrypted_command_request.decode())

                    if not denc_json.success:
                        # print("decryption of command failed")
                        conn.send(bytes("255", encoding='utf-8'))
                        conn.close()
                        continue

                    json_resp = json.loads(denc_json.result.decode('utf-8'))  # convert str to json
                    # print(json_resp)

                    challenge = generate_random_string(16)
                    conn.send(bytes(challenge, encoding='utf-8'))
                    # print("sent challenge "+challenge)

                    challenge_response = conn.recv(1024)
                    # print("received chal response "+challenge_response.decode())

                    card_file_name = get_card_file_name(json_resp)
                    # print("a card file chama-se " + card_file_name)

                    try:
                        card_file_content = open(card_file_name, "r").read()
                    except FileNotFoundError:
                        # print("card file does not exist")
                        conn.close()
                        continue

                    challenge_response_solution = decrypt(key=card_file_content, data=challenge_response.decode())
                    # print("chal response solution "+challenge_response_solution.decode())

                    if not challenge_response_solution.success:
                        # print("decryption of challenge response failed")
                        conn.send(bytes("255", encoding='utf-8'))
                        conn.close()
                        continue

                    current_time = int(time.time_ns())  # nanosecond precision
                   # print("Current time on server is " + str(current_time))

                    expire_date = get_expire_date(json_resp)
                   # print("expire date on msg is " + str(expire_date))

                    if challenge_response_solution.result.decode() == challenge and expire_date > current_time:
                       # print("challenge matches and " + str(expire_date) + ">" + str(current_time))

                        if "create" in json_resp:
                            # print("card hash:",json_resp["create"]["card_hash"])
                            response = new_account(json_resp)
                            if response.success:
                                print(response.result, flush=True)
                                conn.send(bytes(response.result, encoding='utf-8'))
                            else:
                                conn.send(bytes(response.result, encoding='utf-8'))

                            conn.close()
                            continue

                        if "deposit" in json_resp:
                            response = deposit(json_resp)
                            if response.success:
                                print(response.result, flush=True)
                                conn.send(bytes(response.result, encoding='utf-8'))
                            else:
                                conn.send(bytes(response.result, encoding='utf-8'))

                            conn.close()
                            continue

                        if "withdraw" in json_resp:
                            response = withdraw(json_resp)
                            if response.success:
                                print(response.result, flush=True)
                                conn.send(bytes(response.result, encoding='utf-8'))
                            else:
                                conn.send(bytes(response.result, encoding='utf-8'))

                            conn.close()
                            continue

                        if 'get' in json_resp:
                            response = get_balance(json_resp)
                            if response.success:
                                print(response.result, flush=True)
                                conn.send(bytes(response.result, encoding='utf-8'))
                            else:
                                conn.send(bytes(response.result, encoding='utf-8'))

                            conn.close()
                            continue
                    else:
                        conn.send(bytes("255", encoding='utf-8'))
                        conn.close()
                        #s.close()
                        #print("client NOT authenticated, challenge differ or TTL expired")
                except socket.timeout:
                    print("protocol_error", flush=True)
                    conn.close()
                    continue

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


def create_auth_file(filename: str):
    try:
        f = open(filename, "x")
        content = generate_random_string(128)
        f.write(content)
        f.close()
        print("created", flush=True)
    except Exception:
        exit(255)


def validate_args(args) -> Response:
    #  if len(args.filename) > 1 | len(args.port) > 1:
    #     return Response(False, 'Arguments cannot be duplicate')
    return Response(True, args)


def check_double_params(list_of_elements):
    set_of_elements = set()
    for elem in list_of_elements:
        if elem in set_of_elements:
            return True
        else:
            set_of_elements.add(elem)
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
    if is_admin():
        # proper_exit('Error: the script must run as unprivileged/regular user')
        exit(255)

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
