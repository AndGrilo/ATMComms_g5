import os
import re
import sys
import math
import pickle
import base64
import platform
import argparse
from collections import namedtuple

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256


Person = namedtuple('Person', ['group', 'name'])
Event = namedtuple('Event', ['timestamp', 'person', 'action', 'room'])
Response = namedtuple('Response', ['success', 'result'])
SEED = f"|{math.pi:.8f}|{math.e:.8f}"


def encrypt(key: str, data, encode: bool = True):
    salt = str(SHA256.new(str(str(key).swapcase() + SEED).encode('utf-8')).hexdigest())
    key = SHA256.new(str(key + salt).encode('utf-8')).digest()
    iv = Random.new().read(AES.block_size)
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    padding = AES.block_size - len(data) % AES.block_size
    data += bytes([padding]) * padding
    data = iv + encryptor.encrypt(data)
    return base64.b64encode(data).decode('utf-8') if encode else data


def decrypt(key: str, data, decode: bool = True):
    salt = str(SHA256.new(str(str(key).swapcase() + SEED).encode('utf-8')).hexdigest())
    key = SHA256.new(str(key + salt).encode('utf-8')).digest()
    data = base64.b64decode(data.encode('utf-8')) if decode else data
    iv = data[:AES.block_size]
    decryptor = AES.new(key, AES.MODE_CBC, iv)
    data = decryptor.decrypt(data[AES.block_size:])
    padding = data[-1]
    if data[-padding:] != bytes([padding]) * padding:
        raise ValueError("Invalid padding...")
    return data[:-padding]


def create_database(token: str, path: str) -> Response:
    try:
        database = {'last_timestamp': 0, 'people': dict()}
        with os.fdopen(os.open(os.path.abspath(path), os.O_WRONLY | os.O_CREAT, 0o600), 'w') as fout:
            fout.write(encrypt(key=token, data=pickle.dumps(database)))
            return Response(True, 'Database created')
    except IOError:
        return Response(False, 'Error: could not create database file')


def read_database(token: str, path: str) -> Response:
    try:
        with open(os.path.abspath(path), 'r') as fin:
            if platform.system() != 'Windows' and oct(os.stat(path).st_mode & 0o777) != '0o600':
                raise PermissionError('On Linux, database file permission must be 600')
            database = pickle.loads(decrypt(key=token, data=fin.read()))
            return Response(True, database)
    except FileNotFoundError:
        return Response(False, 'Error: database file not found')
    except PermissionError as err:
        message = 'Error: could not read database file due to incorrect file permission'
        if str(err).startswith('On Linux'):
            message += f". {err}"
        return Response(False, message)
    except IOError:
        return Response(False, 'Error: could not read database file')
    except Exception:
        return Response(False, 'Error: integrity violation, invalid token or database file')


def room_type(value):
    min_value, max_value = 0, 1073741823
    if str(value).isdigit() and min_value <= int(value) <= max_value:
        return int(value)
    else:
        raise argparse.ArgumentTypeError(f"invalid room, it must be an int and range from {min_value} to {max_value} (inclusively)")


def timestamp_type(value):
    min_value, max_value = 1, 1073741823
    if str(value).isdigit() and min_value <= int(value) <= max_value:
        return int(value)
    else:
        raise argparse.ArgumentTypeError(f"invalid timestamp, it must be an int and range from {min_value} to {max_value} (inclusively)")


def path_type(value):
    if isinstance(value, str) and not os.path.islink(value):
        return str(value)
    else:
        raise argparse.ArgumentTypeError(f"path must be a string and cannot be a symbolic link")


def name_type(value):
    min_length, max_length = 3, 256
    pattern = r'^[a-zA-Z]+$'
    if isinstance(value, str) and min_length <= len(value) <= max_length and bool(re.match(pattern, value)):
        return str(value)
    else:
        raise argparse.ArgumentTypeError(f"invalid name, it is case-sensitive, must be alpha only between {min_length} and {max_length} chars (inclusive), and cannot contain spaces")


def token_type(value):
    min_chars, min_length, max_length = 3, 16, 256
    type_pattern = r'^[a-zA-Z0-9]+$'
    if isinstance(value, str) and min_length <= len(value) <= max_length and bool(re.match(type_pattern, value)):
        numbers_ok = sum(map(str.isdigit, value)) >= min_chars
        if numbers_ok:
            upper_ok = sum(map(str.isupper, value)) >= min_chars
            if upper_ok:
                lower_ok = sum(map(str.islower, value)) >= min_chars
                if lower_ok:
                    return value

    raise argparse.ArgumentTypeError(f"invalid token, it must be alphanumeric between {min_length} and {max_length} chars (inclusive), and contain at least {min_chars} lowercase, uppercase and digit chars")


def proper_exit(message: str = 'invalid', exit_code: int = 255) -> None:
    print(message)
    sys.exit(exit_code)


def is_admin() -> bool:
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
