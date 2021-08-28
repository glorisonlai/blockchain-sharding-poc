from .models import Wallet, Shard
import random
from .decorators import classproperty

class WalletController:
	_wallets = {}
	def __init__(self, *names: list[str]) -> None:
		WalletController._wallets = {
			name: Wallet(name) for name in names
		}

	@staticmethod
	def users() -> list[str]:
		return list(WalletController._wallets.keys())

	@staticmethod
	def has_user(username: str) -> bool:
		return username in WalletController._wallets 

	@staticmethod
	def get_user(username: str) -> Wallet:
		if username not in WalletController._wallets:
			raise KeyError
		return WalletController._wallets[username]

	@staticmethod
	def wallets() -> list[Wallet]:
		return WalletController._wallets

class ShardController:
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