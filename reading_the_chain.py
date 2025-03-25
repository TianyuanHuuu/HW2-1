import random
import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.providers.rpc import HTTPProvider


def connect_to_eth():
    url = "https://mainnet.infura.io/v3/8054c6b6305148d7be6d257adef7a4e6"
    w3 = Web3(HTTPProvider(url))
    assert w3.is_connected(), f"Failed to connect to provider at {url}"
    return w3


def connect_with_middleware(contract_json):
    with open(contract_json, "r") as f:
        d = json.load(f)
        d = d['bsc']
        address = d['address']
        abi = d['abi']

    # Connect to Binance Smart Chain (BSC) testnet
    url = "https://data-seed-prebsc-1-s1.binance.org:8545"
    w3 = Web3(HTTPProvider(url))
    assert w3.is_connected(), f"Failed to connect to provider at {url}"

    # Inject POA middleware for BSC chains
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    # Create contract object
    contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)

    return w3, contract


def is_ordered_block(w3, block_num):
    block = w3.eth.get_block(block_num, full_transactions=True)
    base_fee = block.get('baseFeePerGas', 0)
    txs = block.transactions

    priority_fees = []

    for tx in txs:
        if tx['type'] == '0x2':
            max_priority = tx.get('maxPriorityFeePerGas', 0)
            max_fee = tx.get('maxFeePerGas', 0)
            priority = min(max_priority, max_fee - base_fee)
        else:
            gas_price = tx.get('gasPrice', 0)
            priority = gas_price - base_fee

        priority_fees.append(priority)

    return priority_fees == sorted(priority_fees, reverse=True)


def get_contract_values(contract, admin_address, owner_address):
    default_admin_role = int.to_bytes(0, 32, byteorder="big")

    onchain_root = contract.functions.merkleRoot().call()
    has_role = contract.functions.hasRole(default_admin_role, Web3.to_checksum_address(admin_address)).call()
    prime = contract.functions.getPrimeByOwner(Web3.to_checksum_address(owner_address)).call()

    return onchain_root, has_role, prime


if __name__ == "__main__":
    admin_address = "0xAC55e7d73A792fE1A9e051BDF4A010c33962809A"
    owner_address = "0x793A37a85964D96ACD6368777c7C7050F05b11dE"
    contract_file = "contract_info.json"

    eth_w3 = connect_to_eth()
    cont_w3, contract = connect_with_middleware(contract_file)

    latest_block = eth_w3.eth.get_block_number()
    london_hard_fork_block_num = 12965000
    assert latest_block > london_hard_fork_block_num, f"Error: the chain never got past the London Hard Fork"

    n = 5
    for _ in range(n):
        block_num = random.randint(1, latest_block)
        ordered = is_ordered_block(eth_w3, block_num)
        if ordered:
            print(f"Block {block_num} is ordered")
        else:
            print(f"Block {block_num} is not ordered")
