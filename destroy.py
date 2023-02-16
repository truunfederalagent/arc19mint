from mint_assets import destroy_asset
from algosdk.v2client import algod


algod_url = 'http://mainnet-api.algonode.network'
headers = {'User-Agent': 'py-algorand-sdk'}
algod_client = algod.AlgodClient(algod_token="", algod_address=algod_url, headers=headers)

assets = [12345, 12346, 12347] # List of asset IDs

for asset in assets:
    print(destroy_asset(algod_client,asset))