from Crypto.Protocol.KDF import PBKDF2
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from random import random

global master_key

#randfunc for RSA keypair generation
def my_rand(n):
    my_rand.counter += 1

    return PBKDF2(master_key, b"my_rand:%d" % my_rand.counter, dkLen=n, count=1)

#returns an RSA key object
def generate_key(password, salt):
	global master_key
	master_key = PBKDF2(password, salt, count=10000)

	my_rand.counter = 0
	RSA_key = RSA.generate(2048, randfunc=my_rand)
	
	return RSA_key

def encrypt(plaintext, key, k = random()):  #key is public key
	return key.encrypt(plaintext.encode("utf-8"),k)

def decrypt (ciphertext, key):
	return key.decrypt(ciphertext)