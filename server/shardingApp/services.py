from .models import Wallet, BlockChain
import time
import functools

def timeit(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		start = time.perf_counter()
		ret = func(*args, **kwargs)
		end = time.perf_counter()
		wrapper.last_time = end - start
		return ret
	wrapper.last_time = 0
	return wrapper

def generate_user_wallet():
	chain = BlockChain()
	user = Wallet('Satoshi')
	priv_key, pub_key = user.generate_rsa_key_pair()
	return {'balance': user.balance, 'privKey': priv_key, 'pubKey': pub_key}

