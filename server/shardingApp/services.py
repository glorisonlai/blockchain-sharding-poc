from Crypto import Signature
from .models import Block, BlockChain, Miner, ShardController, Transaction
from .store import WalletController
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from Crypto.PublicKey import RSA
import multiprocessing as mp
from .decorators import timeit

""" Global chain """
chain = BlockChain()# TODO: Should eventually move over to Redis


""" Global wallets """
wallets = WalletController('Alice', 'Bob' )
# 'Chris', 'David', 'Edgar', 'Phoebe', 'Greg', \
# 	'Harry', 'Ingrid', 'Jason', 'KEVIN', 'Loc', 'Margaret'

""" Global shards """
shards = ShardController



def get_user_wallet_info(username: str) -> dict[str, str]:
	global wallets
	user_wallet = wallets.get_user(username)
	priv_key, pub_key = user_wallet.generate_rsa_key_pair()
	return {
		'user': user_wallet.name,
		'balance': str(user_wallet.balance),
		'shard': user_wallet.shard_id,
		'privKey': priv_key.hex(), 
		'pubKey': pub_key.hex()
	}


def get_user_wallets() -> list[dict]:
	''' 
	Generates new RSA key pair for global wallets, and returns Wallet information and new key pair
	Saves new public key to global wallets, but does NOT save private key

		Returns
			Dictionary with Wallet information, and key pair
	'''
	return map(get_user_wallet_info, wallets.users())


def process_transaction_request(data: dict) -> bool:
	'''  Validates transaction came from user and appends it to Blockchain waiting list 
	We assume all nodes get the transactions in the same order, so all nodes work on a 
	consistent blockchain.
	'''
	transaction_str: str = data['transaction']
	signatureHex: str = data['signature']
	if not (check_blockchain_not_full() and Transaction.validate(transaction_str, signatureHex)):
		return False

	# Transaction is verified - Try to add to chain
	queue_transaction(transaction_str)

	# Transaction is in queue - Prevent payer from double-spending before confirmation
	decrement_pending_transaction_value(transaction_str)
	return True


def queue_transaction(validated_transaction_str: str) -> None:
	global chain
	chain.append_unconfirmed(Transaction.convert_to_bytes(validated_transaction_str))


def decrement_pending_transaction_value(valid_transaction_str: str) -> None:
	amount, user_id, _, _, _ = Transaction.parse_string(valid_transaction_str)
	global wallets
	user_wallet = wallets.get_user(user_id) # Index of username in transaction
	user_wallet.increment_transaction()
	user_wallet.pay(amount)


def check_blockchain_not_full() -> bool:
	global chain
	return not chain.unconfirmed_full()


@timeit
def serial_transaction_request(allocated_miners: int) -> dict:
	''' Start validating blocks
	-- Create Block with Proof_of_Work of tail of BlockChain
	-- Instantiate 10 miners in parallel (Pretend like they're nodes in the network)
	-- Each miner validates the block, then bruteforces a padding that makes the entire 
		block's hash have 4 leading 0's
	-- Each miner signs the block, and returns the Proof of Work
	-- Server saves each signed block to Wait Tree, and after 5 transactions, approves 
		signed Block and executes transaction

	NOTE: We are assuming all nodes are all working off of the same chain
			In reality, this cannot be regulated, since there is no central server.
			However, since in most cases only one block is added to the chain at any
			point in time, and most nodes have a good incentive to keep up to date with
			longest chain, the majority of the nodes will keep the same copy of the 
			blockchain. This makes a server implementation a good approximation 
			of how the actual blockchain works, ASSUMING all nodes are non-adversarial. 

			With adversarial nodes, multiple techniques exist to buffer mined blocks before
			they are accepted, but generally depend on the distributed nature of an actual
			blockchain, and is out of scope for this basic implementation

	NOTE: Ditching mp.pool approach, since we there is no good way to terminate processes cleanly:
		https://stackoverflow.com/questions/36962462/terminate-a-python-multiprocessing-program-once-a-one-of-its-workers-meets-a-cer
	'''
	mined_block_event = mp.Event()
	quit_event = mp.Event()
	global chain
	new_block = Block(chain.last_transaction().block_hash, chain.unconfirmed_head())
	miner_count = min(allocated_miners, mp.cpu_count() - 1)
	for miner_index in range(miner_count):
		p = mp.Process(target=Miner.mine, args=(miner_index, new_block, quit_event, mined_block_event))
		p.start()
	mined_block_event.wait()
	quit_event.set()


def create_transaction_req(payer: dict[str, str], payee: dict[str, str]):
	# Transaction is formatted as <AMOUNT>:<USERNAME>:<PUBLIC_KEY>:<PAYEE>:<NONCE>
	transaction = f"{str(1)}:{payer['user']}:{payer['pubKey']}:{payee['user']}:{str(payer['nonce'])}"
	message = SHA256.new()
	message.update(bytes(transaction, encoding='utf8'))
	priv_key = RSA.import_key(bytes.fromhex(payer['privKey']))
	signature = pkcs1_15.new(priv_key).sign(message)
	signatureHex = signature.hex()

	return transaction, signatureHex



def shard_transaction_request() -> dict:
	pass

def test(transactions):
	global wallets
	users_res = {user: get_user_wallet_info(user) for user in wallets.users()}
	for _ in range(transactions):
		# Get payer/payee pair
		payer = users_res['Alice']
		payee = users_res['Bob']

		# Increment payer nonce
		users_res[payer['user']]['nonce'] = users_res[payer['user']].setdefault('nonce', -1) + 1

		transaction, signatureHex = create_transaction_req(payer, payee)

		process_transaction_request({'transaction': transaction, 'signature': signatureHex})
	mining = serial_transaction_request
	mining(3)
	return mining.last_time


def test2():
	return ShardController.shards
