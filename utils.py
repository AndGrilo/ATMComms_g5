import os
import string
import random
import sys
import math
import base64
from collections import namedtuple

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256


Response = namedtuple('Response', ['success', 'result'])
SEED = f"|{math.pi:.8f}|{math.e:.8f}"


def encrypt(key: str, data, encode: bool = True):
    try:
        key = SHA256.new(key.encode('utf-8')).digest()
        iv = Random.new().read(AES.block_size)
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        padding = AES.block_size - len(data) % AES.block_size
        data += bytes([padding]) * padding
        data = iv + encryptor.encrypt(data)
        return base64.b64encode(data).decode('utf-8') if encode else data
    except Exception as err:
        print(err)


def decrypt(key: str, data, decode: bool = True) -> Response:
    try:
        key = SHA256.new(key.encode('utf-8')).digest()
        data = base64.b64decode(data.encode('utf-8')) if decode else data
        iv = data[:AES.block_size]
        decryptor = AES.new(key, AES.MODE_CBC, iv)
        data = decryptor.decrypt(data[AES.block_size:])
        padding = data[-1]
        if data[-padding:] != bytes([padding]) * padding:
            # raise ValueError("Invalid padding...")
            return Response(False, 'invalid padding')

        return Response(True, data[:-padding])
    except Exception:
        return Response(False, 'invalid padding')


def generate_random_string(str_size: int):
    characters = list(string.ascii_letters + string.digits + "!@#$%^&*()")
    random.shuffle(characters)
    password = []
    for i in range(str_size):
        password.append(random.choice(characters))
    random.shuffle(password)
    result = "".join(password)

    return result


def proper_exit(message: str = 'invalid', exit_code: int = 255) -> None:
    print(message)
    sys.exit(exit_code)


def is_admin() -> bool:
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
