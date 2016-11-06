import binascii
import os


def create_token():
    return binascii.hexlify(os.urandom(16)).decode()

