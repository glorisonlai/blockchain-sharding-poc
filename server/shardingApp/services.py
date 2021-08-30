from .models import Block, Miner, ShardController, WalletController
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from Crypto.PublicKey import RSA
import multiprocessing as mp
from .decorators import timeit
import random
from queue import Queue


""" Global Blockchain network """
wallets = WalletController(['Alice', 'Bob'] )
# 'Chris', 'David', 'Edgar', 'Phoebe', 'Greg', \
# 	'Harry', 'Ingrid', 'Jason', 'Kevin', 'Loc', 'Margaret'

""" Global Sharded network """
shards = ShardController('Alice', 'Bob', 'Chris', 'David', 'Edgar', 'Phoebe')
# 'Chris', 'David', 'Edgar', 'Phoebe', 'Greg', \
# 	'Harry', 'Ingrid', 'Jason', 'Kevin', 'Loc', 'Margaret'


def get_user_wallets() -> list[dict[str, str]]:
	''' 
	Generates new RSA key pair for global wallets, and returns Wallet information and new key pair
	Saves new public key to global wallets, but does NOT save private key

		Returns
			Dictionary with Wallet information, and key pair
	'''
	return list(map(wallets.get_user_wallet_info, wallets.users()))


def process_serial_transaction_request(data: dict) -> bool:
	'''  Validates transaction came from user and appends it to Blockchain waiting list 
	We assume all nodes get the transactions in the same order, so all nodes work on a 
	consistent blockchain.
	'''
	transaction_str: str = data['transaction']
	signatureHex: str = data['signature']
	if not (transaction_str and signatureHex):
		return False
	return wallets.process_transaction_request(transaction_str, signatureHex)


def process_sharded_transaction_request(data: dict) -> bool:
	transaction_str: str = data['transaction']
	signature_hex: str = data['signature']
	str_shard_id: str = data['shardId']
	if not (transaction_str and signature_hex and str_shard_id):
		return False
	try:
		shard_id = int(str_shard_id)
	except ValueError:
		return False
	if not shards.valid_shard_id(shard_id):
		return False
	return shards.send_transaction_request(shard_id, transaction_str, signature_hex)



@timeit
def serial_transaction_request(allocated_miners: int, network: WalletController) -> dict:
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
	print("⛏️  Starting Mining... ⛏️")
	while not network.chain.unconfirmed_empty():
		# manager = mp.Manager()
		mined_block_event = mp.Event()
		quit_event = mp.Event()
		# ret_queue = Queue()
		# blah = Queue()
		new_block = Block(network.chain.last_transaction().block_hash, network.chain.unconfirmed_head())
		miner_count = min(allocated_miners, mp.cpu_count() - 1)
		for miner_index in range(miner_count):
			p = mp.Process(target=Miner.mine, args=(miner_index, new_block, quit_event, mined_block_event))
			p.start()
		mined_block_event.wait()
		quit_event.set()
		# network.chain.append_to_chain(ret_queue.get())


@timeit
def shard_transaction_request() -> dict:
	# for shard in shards.shards:
	# 	p = mp.Process(target=serial_transaction_request, args=(1, shard))
	# 	p.start()
	shard_pool = mp.Pool(processes = shards.num_shards)
	shard_pool.map(shard_transaction_request, [(1, shard) for shard in shards.shards])
	shard_pool.close()
	shard_pool.join()


def create_transaction_req(payer: dict[str, str], payee: dict[str, str]):
	# Transaction is formatted as <AMOUNT>:<USERNAME>:<PUBLIC_KEY>:<PAYEE>:<NONCE>
	transaction = f"{str(1)}:{payer['user']}:{payer['pubKey']}:{payee['user']}:{str(payer['nonce'])}"
	message = SHA256.new()
	message.update(bytes(transaction, encoding='utf8'))
	priv_key = RSA.import_key(bytes.fromhex(payer['privKey']))
	signature = pkcs1_15.new(priv_key).sign(message)
	signatureHex = signature.hex()

	return transaction, signatureHex


def test_serial(transactions: int) -> int:
	users_res = get_user_wallets()
	for _ in range(transactions):
		payer_index = random.randrange(0, len(users_res))
		payee_index = random.randrange(0, len(users_res)-1)
		if payee_index >= payer_index:
			payee_index += 1
		# Get payer/payee pair
		payer = users_res[payer_index]
		payee = users_res[payee_index]

		# Increment payer nonce
		payer['nonce'] = payer.setdefault('nonce', -1) + 1

		transaction, signatureHex = create_transaction_req(payer, payee)

		process_serial_transaction_request({'transaction': transaction, 'signature': signatureHex})
	mining = serial_transaction_request
	mining(5, wallets)
	return mining.last_time


def test_shard(transactions: int) -> int:
	users_res: list[list[dict[str, str]]] = []
	for shard_id in range(shards.num_shards):
		users_res.append([shards.get_user_wallet_info(shard_id, user) for user in shards.get_shard_users(shard_id)])
	for _ in range(transactions):
		shard_index = random.randrange(0, shards.num_shards)
		payer_index = random.randrange(0, len(users_res[shard_index]))
		payee_index = random.randrange(0, len(users_res[shard_index])-1)
		if payee_index >= payer_index:
			payee_index += 1
		# Get payer/payee pair
		payer = users_res[shard_index][payer_index]
		payee = users_res[shard_index][payee_index]

		# Increment payer nonce
		payer['nonce'] = payer.setdefault('nonce', -1) + 1

		transaction, signatureHex = create_transaction_req(payer, payee)

		process_sharded_transaction_request({'transaction': transaction, 'signature': signatureHex, 'shardId': str(payer['shardId'])})
	mining = shard_transaction_request
	mining()
	return mining.last_time
