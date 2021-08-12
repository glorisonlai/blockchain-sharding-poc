from .models import Wallet, BlockChain

chain = None # Might need redis, or some state service :(

def generate_user_wallet():
	chain = BlockChain()
	user = Wallet('Satoshi')
	return user.generate_rsa_key_pair()