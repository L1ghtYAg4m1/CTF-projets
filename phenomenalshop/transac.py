from web3 import Web3

# Connect to local Ethereum testnet (e.g., Ganache)
web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Check if connected to Ganache
if web3.is_connected():
    print("Connected to Ganache")
else:
    print("Failed to connect to Ganache")

# Fetch the latest block and print its transactions
latest_block = web3.eth.get_block('latest', full_transactions=True)

# Display information about the latest block
print(f"Block Number: {latest_block['number']}")
print(f"Transactions in Block: {latest_block['transactions']}")

# Iterate over transactions in the latest block and print details
for tx in latest_block['transactions']:
    print(f"Transaction: {tx}")
