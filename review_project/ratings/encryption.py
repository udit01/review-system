from Crypto.Protocol.KDF import PBKDF2
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from random import random
import base64

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
	print("ENCRYPTING-",plaintext)
	publickey=RSA.importKey(key)
	encrypted_msg = publickey.encrypt(plaintext.encode('utf-8'), 32)[0]
	encoded_encrypted_msg = base64.b64encode(encrypted_msg) # base64 encoded strings are database friendly
	return encoded_encrypted_msg

def decrypt (ciphertext, key):
	privatekey=RSA.importKey(key)
	decoded_encrypted_msg = base64.b64decode(ciphertext)
	print("DECRYPTING-",decoded_encrypted_msg)
	decoded_decrypted_msg = privatekey.decrypt(decoded_encrypted_msg)
	return decoded_decrypted_msg.decode('utf-8')