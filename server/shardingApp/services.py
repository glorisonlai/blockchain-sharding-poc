from .models import Wallet, BlockChain, Shard
import time
import functools

SHARDS = 2
OCCUPATIONS = 2

# Accessing chain globally to avoid setting up DB
# Should eventually move over to Redis
chain = BlockChain()

wallets = [
	Wallet('Alice'),
	Wallet('Bob'),
	Wallet('Chris'),
	Wallet('User'),
]

def instantiate_shards(wallets, shard_count, occ_count): 
	shards = [Shard(occ_count)] * shard_count


shards = instantiate_shards(wallets, shard_count=SHARDS, occ_count=OCCUPATIONS)



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
	user = Wallet('Satoshi')
	priv_key, pub_key = user.generate_rsa_key_pair()
	return {'balance': user.balance, 'privKey': priv_key, 'pubKey': pub_key}

