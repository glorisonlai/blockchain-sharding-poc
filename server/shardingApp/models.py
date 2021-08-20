from django.db import models
from Crypto.PublicKey import RSA
import multiprocessing as mp

class Wallet:
	def __init__(self, username: str) -> None:
		self.name: str = username
		self.balance: int = 100
		self.pub_key: str = ''
		self.generate_rsa_key_pair()

	def generate_rsa_key_pair(self) -> tuple[bytes,bytes]:
		key = RSA.generate(2048)
		self.pub_key = key.public_key()
		return (key.export_key('PEM'), key.public_key().export_key('PEM'))

class Block:
	def __init__(self, prev: bytes, transaction: bytes):
		self.prev = prev
		self.transaction = transaction

class Transaction:
	def __init__(self, bytes):
		self.bytes = bytes

	def validate_byte_format(self):
		return True

class BlockChain:
	shards = 10
	occupations = 5

	def __init__(self):
		self.__chain = [Block(b'', b'')]
	
	def head(self):
		return self.__chain[-1]

class Shard:
	def __init__(self, occupations: int):
		self.__occupations: list[Wallet] = [None] * occupations

class ShardController:
	def __init__(self, shard_count, occ_count):
		self.__shards = [Shard(occ_count)] * shard_count

	def allocate_wallets(self, wallets):
		for index, wallet in enumerate(wallets):
			self.__shards[index % len(self.__shards)].allocate

