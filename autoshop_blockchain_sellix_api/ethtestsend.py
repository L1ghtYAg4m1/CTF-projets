from web3 import Web3

# Connect to local Ethereum testnet (e.g., Ganache)
web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Check if the connection is successful
if web3.is_connected():
    print("Connected to Ethereum")
else:
    print("Failed to connect to Ethereum")

# Get the nonce (transaction count) for the sending address
sender_address = '0xF57131Cc74Fbcbd315765FFCcb75A116f761375A'
nonce = web3.eth.get_transaction_count(sender_address)

# Specify the transaction details
transaction = {
    'from': sender_address,                                # Sender address
    'to': '0x7FBF155551c5ad38c979FA2Cf280719d4842107A',    # Receiver address
    'value': web3.to_wei(1, 'ether'),                      # Amount to send in Wei (1 ETH)
    'gas': 21000,                                          # Gas limit for standard transactions
    'gasPrice': web3.to_wei('20', 'gwei'),                 # Gas price in Gwei
    'nonce': nonce                                         # Include the nonce
}

# Replace this with the private key of the sender (DO NOT SHARE IT PUBLICLY)
private_key = '0x917e932672d1c0098810fcbc304a4077c243ee0ceecf38eb0760a419c1131f39'

# Sign the transaction
signed_tx = web3.eth.account.sign_transaction(transaction, private_key)

# Send the transaction using the correct attribute 'raw_transaction'
tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

# Wait for the transaction to be mined
receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

# Log the transaction receipt
print(f'Transaction hash: {web3.to_hex(tx_hash)}')
print(f'Transaction receipt: {receipt}')
