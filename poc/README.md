# POC of Sharding interaction

## Files

`users.txt` Contains User wallet information, including balance, shard ID, public key and private key.

`initialTransactions.ts` Creates serialized transactions signed with User private keys. Saves to `initial-transactions.txt`

`sharding.py` Reads from `initial-transactions.txt` and validates and appends transactions to blockchain in parallel via sharding. Prints times out to `transaction-shard-times.txt`

`serial.py` Reads from `initial-transactions.txt` and validates and appends transactions to blockchain serially. Prints times out to `transaction-serial-times.txt`
