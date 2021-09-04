from shardingApp.services import test_serial, test_shard

if __name__ == '__main__':
	print(f'Serial POC: {int(test_serial(10) * 100) / 100}s')
	print()
	print(f'Sharding POC: {int(test_shard(10) * 100) / 100}s')