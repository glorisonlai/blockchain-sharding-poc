from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from queue import Queue
import random
from .decorators import classproperty
from time import sleep
from multiprocessing.synchronize import Event


class Wallet:
	'''
	Class storing public wallet information

	Attributes
		_name: str
			Unique ID of wallet
		_balance: int
			Amount usable in transactions. Should point to last transaction for proof
		_pub_key: bytes
			RSA PEM public key
		_shard_id: int
			Network wallet belongs to
		_transactions: int
			Nonce to verify transactions
	'''
	def __init__(self, username: str, shard_id: int) -> None:
		self._name = username
		self._balance = 100
		self._pub_key = b''
		self._shard_id = shard_id
		self._transactions = 0
		self.generate_rsa_key_pair()


	def generate_rsa_key_pair(self) -> tuple[bytes,bytes]:
		""" Generates and exports RSA key pair in PEM format """
		key = RSA.generate(2048)
		self._pub_key = key.public_key().export_key('PEM')
		return (key.export_key('PEM'), key.public_key().export_key('PEM'))


	@property
	def name(self) -> str:
		""" Getter for wallet ID """
		return self._name


	@property
	def balance(self) -> int:
		""" Getter for wallet balance """
		return self._balance
	

	def pay(self, decrement: int) -> None:
		''' 
		Decrease wallet balance by decrement

		Argument
			decrement: Amount to reduce balance by
		
		Raises 
			ValueError if decrement is malformed or wallet does not have balance
		'''
		if not isinstance(decrement, int) or abs(decrement) > self._balance:
			raise ValueError
		self._balance -= decrement


	@property
	def pub_key(self) -> str:
		""" Getter for wallet public key """
		return self._pub_key


	@property
	def shard_id(self) -> int:
		""" Getter for wallet network ID """
		return self._shard_id


	@shard_id.setter
	def shard_id(self, new_shard_id: int) -> None:
		""" Setter for wallet network ID """
		if not isinstance(new_shard_id, int) or new_shard_id < 0:
			raise ValueError
		self._shard_id = new_shard_id


	def correct_nonce(self, nonce) -> bool:
		""" Verifies nonce in transaction matches current wallet nonce """
		return nonce == self._transactions


	def increment_transaction(self) -> None:
		""" Increment wallet nonce """
		self._transactions += 1


	def enough_balance(self, decrement: int) -> bool:
		""" Verifies wallet balance can fulfill decrement """
		return decrement > 0 or decrement > self.balance


class WalletController():
	'''
	Class simulating single blockchain network

	Attributes
		_wallets: dict[str, Wallet]
			Dictionary of ID, Wallet keypairs in network
		_chain: Blockchain
			Synced blockchain associated with wallets
	'''
	def __init__(self, names: list[str], shard_id = -1) -> None:
		self._wallets = {
			name: self.create_user(name, shard_id) for name in names
		}
		self._chain = BlockChain()


	@property
	def chain(self):
		""" Getter for blockchain """
		return self._chain


	def users(self) -> list[str]:
		""" Returns list of wallet names """
		return list(self._wallets.keys())


	def create_user(self, username: str, shard_id: int) -> Wallet:
		''' 
		Create new Wallet object
		Does not allow direct modification to existing users
		'''
		if username in self._wallets:
			raise KeyError
		return Wallet(username, shard_id)


	def can_pay(self, payer: str, payee: str) -> bool:
		''' Verifies payer and payee can trasact
		Payer and payee have different IDs
		Payer exists in network
		Payee exists in network
		'''
		return payer != payee and \
			payer in self._wallets and \
			payee in self._wallets


	def get_user(self, username: str) -> Wallet:
		""" Get wallet associated with ID """
		if username not in self._wallets:
			raise KeyError
		return self._wallets[username]


	def get_user_wallet_info(self, username: str) -> dict[str, str]:
		''' Generates new RSA key pair for user and stores new public key
		Sends client wallet information, including key pair
		'''
		user_wallet = self.get_user(username)
		priv_key, pub_key = user_wallet.generate_rsa_key_pair()
		return {
			'user': user_wallet.name,
			'balance': str(user_wallet.balance),
			'shardId': user_wallet.shard_id,
			'privKey': priv_key.hex(), 
			'pubKey': pub_key.hex()
		}
	

	def process_transaction_request(self, transaction_str: str, signature_hex: str) -> bool:
		'''  Validates transaction came from user and appends it to Blockchain waiting list 
		Eagerly remove transaction amount from user balance to prevent double spending

		NOTE: Assume all nodes get the transactions in the same order, so all nodes work on a 
		consistent blockchain.
		'''
		transaction_chk = Transaction(self)
		if not (transaction_chk.validate(transaction_str, signature_hex) and self.check_mempool_not_full()):
			return False

		# Transaction is verified - Try to add to chain
		self._queue_transaction(transaction_str)

		# Transaction is in queue - Prevent payer from double-spending before confirmation
		self._decrement_pending_transaction_value(transaction_str)
		return True


	def _queue_transaction(self, validated_transaction_str: str) -> None:
		""" Append transaction to mempool """
		self._chain.append_unconfirmed(Transaction.convert_to_bytes(validated_transaction_str))


	def _decrement_pending_transaction_value(self, valid_transaction_str: str) -> None:
		""" Decrement transaction amount from payer's wallet balance """
		amount, user_id, _, _, _ = Transaction.parse_string(valid_transaction_str)
		user_wallet = self.get_user(user_id) # Index of username in transaction
		user_wallet.increment_transaction()
		user_wallet.pay(amount)


	def check_mempool_not_full(self) -> bool:
		""" Check mempool is not full"""
		return not self._chain.unconfirmed_full()


class ShardController():
	'''
	Class simulating sharded blockchain network

	Attributes:
		_num_shards: int
			Number of sharded networks. 
			Maximum of 3, Minimum of 1 (Network has only one user)
		_shards: list[WalletController]
			List of shard networks
	'''
	def __init__(self, *wallets: list[str]) -> None:
		self._num_shards = min(3, len(wallets))
		self._shards = self._allocate_wallets(wallets)


	def _allocate_wallets(self, wallets: tuple[str]) -> list[WalletController]:
		'''
		Allocates wallets evenly depending on number of shards supported
		If 5 wallets are distributed among 3 shards, first 2 shards will each have 1 extra wallet.

		Arguments:
			wallets: list[str]
				List of wallet IDs to allocate
		'''
		shards_list: list[WalletController] = []
		num_shards = self.num_shards
		wallets_per_shard = len(wallets) // num_shards
		rem_wallets = len(wallets) % num_shards
		start_index = 0

		for shard_id in range(num_shards):
			shards_list.append(WalletController(wallets[start_index: \
				start_index + wallets_per_shard + (1 if rem_wallets else 0)], shard_id))
			start_index += wallets_per_shard + (1 if rem_wallets else 0)
			if rem_wallets: rem_wallets -= 1
		return shards_list


	def valid_shard_id(self, shard_id: int) -> bool:
		""" Verifies requested shard_id is valid """
		return isinstance(shard_id, int) and \
			shard_id >= 0 and \
			shard_id < self.num_shards


	def get_shard_users(self, shard_id: int) -> list[str]:
		""" Get list of wallet IDs in shard_id """
		return self._shards[shard_id].users()


	def get_user_wallet_info(self, shard_id: int, username: str) -> dict[str, str]:
		""" Get public wallet information of user in shard_id """
		return self._shards[shard_id].get_user_wallet_info(username)


	def send_transaction_request(self, shard_id: int, transaction_str: str, signature_hex: str) -> bool:
		""" Send transaction request data to shard """
		return self._shards[shard_id].process_transaction_request(transaction_str, signature_hex)


	@property
	def shards(self):
		""" Getter for shard network """
		return self._shards


	@property
	def num_shards(self):
		""" Getter for number of shards in network """
		return self._num_shards


class Transaction:
	'''
	Class storing methods to parse and validate transaction request

	Attributes:
		network: WalletController
			Network request is tied to
	'''
	def __init__(self, cls: WalletController) -> None:
		self.network = cls


	def validate(self, transaction_str: str, signature_hex: str) -> bool:
		'''
		Parses transaction for relevant information.
		Verifies signature of transaction
		Verifies transaction stakeholders and amount
		'''
		try:
			amount, user_id, public_key, payee, nonce = self.parse_string(transaction_str)
		except ValueError:
			return False
		return (self.verify_signature(transaction_str, public_key, signature_hex) and \
			self.validate_transaction(amount, user_id,public_key, payee, nonce))


	@staticmethod
	def convert_to_bytes(transaction: str) -> bytes:
		""" Returns bytes of encoded string """
		return bytes(transaction, encoding='utf8')


	@staticmethod
	def parse_string(transaction_str: str) -> tuple[int, str, bytes, str, int]:
		''' 
		Parses transaction for relevant information and casts to correct type.
		Transaction is formatted as <AMOUNT>:<USERNAME>:<PUBLIC_KEY>:<PAYEE>:<NONCE>

		Arguments
			transaction_str -- String representation of transaction formatted as above
		
		Returns
			Tuple of typed transaction values

		Throws
			ValueError if transacton_str is formatted incorrectly
		'''
		transaction_str_tokens = transaction_str.split(':')
		amount, user_id, public_key, payee, nonce = transaction_str_tokens
		public_key = bytes.fromhex(public_key)
		amount = int(amount)
		nonce = int(nonce)

		return amount, user_id, public_key, payee, nonce


	@staticmethod
	def verify_signature(transaction_str: str, public_key: bytes, signatureHex: str) -> bool:
		''' Checks:
		-- Transaction, public key and Signature exist
		-- Signature verifies original sender 
		'''
		if not (transaction_str and public_key and signatureHex): return False
		signature = bytes.fromhex(signatureHex)
		try:
			sig_verify = SHA256.new()
			sig_verify.update(bytes(transaction_str, encoding='utf8'))
			RSA_public_key = RSA.import_key(public_key)
			pkcs1_15.new(RSA_public_key).verify(sig_verify, signature)
			return True
		except (ValueError, TypeError):
			return False


	def validate_transaction(self, amount: int, user_id: str, public_key: bytes, payee: str, nonce: int) -> bool:
		""" Passes data to validator methods """
		return (self.validate_stakeholders(user_id, public_key, payee) and \
			self.validate_amount(amount, user_id, nonce))


	def validate_stakeholders(self, user_id: str, public_key: bytes, payee: str) -> bool:
		''' Checks:
		-- Username and Payee exists in wallets
		-- Username and Payee are not the same person
		-- Username and Public Key matches info in Wallet store
		'''
		return self.network.can_pay(user_id, payee) and \
			self.network.get_user(user_id).pub_key == public_key and \
			self.network.get_user(user_id).name == user_id
			

	def validate_amount(self, amount: int, user_id: str, nonce: int) -> bool:
		''' Checks:
		-- Nonce was not previously used
		-- Amount is not negative, 0, or exceeds balance
		'''
		user_wallet = self.network.get_user(user_id)
		return amount > 0 and \
			user_wallet.correct_nonce(nonce) and \
			user_wallet.enough_balance(amount)


class Block:
	''' 
	Class storing unit of Blockchain information

	Attributes
		_prev_hash: bytes
			Hash of previous block
		_transaction: bytes
			Encoded associated transaction string. Can be extended to be a list of transactions
		_nonce: bytes
			Random bytes to be modified to change hash of block
		_block_hash: bytes
			Hash of the block. For block to be accepted, must have appropriate number of leading 0's.
	'''
	def __init__(self, prev_proof_of_work: bytes, transaction: bytes) -> None:
		self._prev_hash = prev_proof_of_work
		self._transaction = transaction
		self._nonce = b''
		self._block_hash = b''
		self.calculate_block_hash()


	@property
	def block_hash(self) -> bytes:
		""" Getter for current block hash """
		return self._block_hash

	@property
	def nonce(self) -> bytes:
		""" Getter for current block nonce """
		return self._nonce


	@nonce.setter
	def nonce(self, new_bytes) -> None:
		""" Setter for block nonce """
		if not isinstance(new_bytes, bytes):
			raise TypeError
		self._nonce = new_bytes
		self.calculate_block_hash()


	def calculate_block_hash(self) -> None:
		""" Calculates new block hash and updates existing block_hash attribute """
		message = SHA256.new()
		message.update(self._prev_hash)
		message.update(self._transaction)
		message.update(self._nonce)
		self._block_hash = message.digest()


class BlockChain:
	'''
	Class representing blockchain

	Attributes
		_chain: list[Block]
			List of accepted blocks
			Blockchain always contains 'Genesis' block for other blocks to build off of
		_unconfirmed_transactions: Queue[Transaction]
			Mempool of validated transactions
			Transaction must be pushed into Block and mined before it is accepted into the Blockchain
	'''
	def __init__(self) -> None:
		self._chain = [Block(b'', b'Genesis')]
		self._unconfirmed_transactions: Queue[Transaction] = Queue()
	

	def last_transaction(self) -> Block:
		""" Getter for last transaction in blockchain """
		return self._chain[-1]

	
	def append_to_chain(self, block: Block) -> None:
		""" Setter to append Block to blockchain """
		self._chain.append(block)


	def unconfirmed_full(self) -> bool:
		""" Checks if mempool is full """
		return self._unconfirmed_transactions.full()


	def unconfirmed_empty(self) -> bool:
		""" Checks if mempool is empty """
		return self._unconfirmed_transactions.empty()


	def unconfirmed_head(self) -> Transaction:
		""" Fetches transaction from mempool """
		if self._unconfirmed_transactions.empty():
			raise IndexError
		return self._unconfirmed_transactions.get()


	def append_unconfirmed(self, transaction: Transaction) -> None:
		""" Appends transaction into mempool"""
		if self._unconfirmed_transactions.full():
			raise IndexError
		self._unconfirmed_transactions.put(transaction)


# class Shard(WalletController):
# 	'''
#	WIP
# 	Subclass of WalletController
# 	Buffers cross-shard transactions and sends swap transaction first.
# 	When Swap transaction is accepted into the blockchain, associated transaction can then be verified

# 	Attributes
# 		_num_occupations: int
# 			Number of 'Juries' to validate mining attempt

# 	TODO: Implement Contract protocol to fulfill swap transactions
# 	'''
# 	_num_occupations = 2

# 	def __init__(self, wallets: list[str]) -> None:
# 		self._occupations: list[Wallet] = [] * Shard._num_occupations
	

# 	def allocate_occupation(self, wallet: Wallet) -> None:
# 		allocated_occ = random.randint(0, len(self._occupations)-1)
# 		self._occupations[allocated_occ].append(wallet)


# 	@property
# 	def shard_wallets(self):
# 		return self._occupations


class Miner:
	''' 
	Miner class modifies nonce of block until accepted hash is found
	'''
	_mining_difficulty = 2

	@staticmethod
	def mine(id: int, block: Block, quit_signal: Event, mined_signal: Event) -> None:
		iterations = 0
		print(id)
		# sleep(5)
		# print(f'{id} finsihed sleeping')
		while not quit_signal.is_set():
			if (any(block.block_hash[byte_index] != 0 \
				for byte_index in range(Miner.mining_difficulty))):
				iterations += 1
				# block.nonce = os.urandom(5)
				block.nonce = random.randbytes(10)
			else:
				# queue.put(block)
				mined_signal.set()
				print(f'Miner #{id} mined in {iterations} iterations!')
		return


	@classproperty
	def mining_difficulty(self) -> int:
		return self._mining_difficulty