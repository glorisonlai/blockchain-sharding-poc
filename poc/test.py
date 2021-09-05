from src.services import test_serial, test_shard

if __name__ == '__main__':
	transactions = 10 # Transactions generated and mined. Change this to make tests go faster
	print(f'Serial POC: {int(test_serial(10) * 100) / 100}s')
	print()
	print(f'Sharding POC: {int(test_shard(10) * 100) / 100}s')