from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from queue import Queue
import random
from .decorators import classproperty


class Wallet:
	def __init__(self, username: str) -> None:
		self._name: str = username
		self._balance: int = 100
		self._pub_key: bytes = b''
		self._shard_id: int = -1
		self._transactions = 0
		self.generate_rsa_key_pair()


	def generate_rsa_key_pair(self) -> tuple[bytes,bytes]:
		key = RSA.generate(2048)
		self._pub_key = key.public_key().export_key('PEM')
		return (key.export_key('PEM'), key.public_key().export_key('PEM'))


	@property
	def name(self) -> str:
		return self._name


	@property
	def balance(self) -> int:
		return self._balance
	

	def pay(self, decrement: int) -> None:
		if not isinstance(decrement, int) or abs(decrement) > self._balance:
			raise ValueError
		self._balance -= decrement


	@property
	def pub_key(self) -> str:
		return self._pub_key


	@property
	def shard_id(self) -> int:
		return self._shard_id


	@shard_id.setter
	def shard_id(self, new_shard_id: int) -> None:
		if not isinstance(new_shard_id, int) or new_shard_id < 0:
			raise ValueError
		self._shard_id = new_shard_id


	def correct_nonce(self, nonce) -> bool:
		return nonce == self._transactions


	def increment_transaction(self) -> None:
		self._transactions += 1


	def enough_balance(self, decrement: int) -> bool:
		return decrement > 0 or decrement > self.balance


class NodeNetwork:
	""" Interface for WalletController and ShardController to implement. Helps with type hinting"""
	def users(self) -> list[str]:
		raise NameError

	def can_pay(self, payer: str, payee: str) -> bool:
		return NameError

	def get_user(self, username: str) -> Wallet:
		return NameError

	def wallets(self) -> list[Wallet]:
		return NameError


class WalletController(NodeNetwork):
	"""
	Class to store wallets and provide methods to access or find wallets
	Stores synced blockchain associated with wallets
	"""
	def __init__(self, *names: list[str]) -> None:
		self._wallets = {
			name: Wallet(name) for name in names
		}
		self._chain = BlockChain()

	def users(self) -> list[str]:
		return list(self._wallets.keys())

	def can_pay(self, payer: str, payee: str) -> bool:
		return payer != payee and \
			payer in self._wallets and \
			payee in self._wallets

	def get_user(self, username: str) -> Wallet:
		if username not in self._wallets:
			raise KeyError
		return self._wallets[username]

	def wallets(self) -> list[Wallet]:
		return self._wallets


class ShardController(NodeNetwork):
	_num_shards = 3
	
	def __init__(self, wallets) -> None:
		self._shards: list[Shard] = [Shard()] * self._num_shards
		self._allocate_wallets(wallets)


	def _allocate_wallets(self, wallets: list[Wallet]) -> None:
		for wallet in wallets:
			allocated_shard = random.randint(0, len(self._shards)-1)
			wallet.shard_id = allocated_shard
			self._shards[allocated_shard].allocate_occupation(wallet)


	def get_shard_wallets(self, shard_id) -> list[Wallet]:
		if shard_id < 0 or shard_id > len(self._shards):
			return []
		return self._shards[shard_id].shard_wallets

	@classproperty
	def shards(cls):
		return ShardController._num_shards


class Transaction:
	def __init__(self, cls: NodeNetwork) -> None:
		self.network = cls


	def validate(self, transaction_str: str, signatureHex: str) -> bool:
		try:
			amount, user_id, public_key, payee, nonce = self.parse_string(transaction_str)
		except ValueError:
			return False
		return (self.verify_signature(transaction_str, public_key, signatureHex) and \
			self.validate_transaction(amount, user_id,public_key, payee, nonce))


	@staticmethod
	def convert_to_bytes(transaction: str) -> bytes:
		return bytes(transaction, encoding='utf8')


	@staticmethod
	def parse_string(transaction_str: str) -> tuple[int, str, bytes, str, int]:
		''' Return transaction is formatted as <AMOUNT>:<USERNAME>:<PUBLIC_KEY>:<PAYEE>:<NONCE>

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
		'''
		-- Transaction and Signature exist
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
		-- Amount is not negative, 0, or exceeds max size
		-- Nonce was not previously used

			Arguments
				Transaction -- String representation of transaction, formatted as above

			Returns
				True if request passes all checks
		'''
		user_wallet = self.network.get_user(user_id)
		return amount > 0 and \
			user_wallet.correct_nonce(nonce) and \
			user_wallet.enough_balance(amount)


class Block:
	def __init__(self, prev_proof_of_work: bytes, transaction: bytes) -> None:
		self._prev_hash = prev_proof_of_work
		self._transaction = transaction
		self._nonce = b''
		self._block_hash = b''
		self.calculate_block_hash()


	@property
	def block_hash(self) -> bytes:
		return self._block_hash

	@property
	def nonce(self) -> bytes:
		return self._nonce

	@nonce.setter
	def nonce(self, new_bytes) -> None:
		if not isinstance(new_bytes, bytes):
			raise TypeError
		self._nonce = new_bytes
		self.calculate_block_hash()

	def calculate_block_hash(self) -> None:
		message = SHA256.new()
		message.update(self._prev_hash)
		message.update(self._transaction)
		message.update(self._nonce)
		self._block_hash = message.digest()


class BlockChain:
	def __init__(self) -> None:
		self._chain = [Block(b'', b'Genesis')]
		self._unconfirmed_transactions: Queue[Transaction] = Queue()
	

	def last_transaction(self) -> Block:
		return self._chain[-1]


	def unconfirmed_full(self) -> bool:
		return self._unconfirmed_transactions.full()


	def unconfirmed_empty(self) -> bool:
		return self._unconfirmed_transactions.empty()


	def unconfirmed_head(self) -> Transaction:
		if self._unconfirmed_transactions.empty():
			raise IndexError
		return self._unconfirmed_transactions.get()


	def append_unconfirmed(self, transaction: Transaction) -> None:
		if self._unconfirmed_transactions.full():
			raise IndexError
		self._unconfirmed_transactions.put(transaction)


class Shard:
	_num_occupations = 2

	def __init__(self) -> None:
		self._occupations: list[Wallet] = [] * Shard._num_occupations
	

	def allocate_occupation(self, wallet: Wallet) -> None:
		allocated_occ = random.randint(0, len(self._occupations)-1)
		self._occupations[allocated_occ].append(wallet)


	@property
	def shard_wallets(self):
		return self._occupations


class Miner:
	_mining_difficulty = 2

	def mine(self, id: int, block: Block, quit_signal, mined_signal) -> Block:
		iterations = 0
		while not quit_signal.is_set():
			if (any(block.block_hash[byte_index] != 0 \
				for byte_index in range(self.mining_difficulty))):
				iterations += 1
				# block.nonce = os.urandom(5)
				block.nonce = random.randbytes(10)
			else:
				mined_signal.set()
				print(f'Miner #{id} mined in {iterations} iterations!')
				# sleep(1)
				return block
		return None

	@classproperty
	def mining_difficulty() -> int:
		return Miner._mining_difficulty