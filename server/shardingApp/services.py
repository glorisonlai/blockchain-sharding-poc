from .models import Wallet, BlockChain

def generate_user_wallet():
	chain = BlockChain()
	user = Wallet('Satoshi')
	priv_key, pub_key = user.generate_rsa_key_pair()
	return {'balance': user.balance, 'privKey': priv_key, 'pubKey': pub_key}
