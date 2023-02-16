from mint_assets import mint_arc_19, update_arc_19
from algosdk.v2client import algod
import json, pandas as pd
from PIL import Image

algod_url = 'http://mainnet-api.algonode.network'
headers = {'User-Agent': 'py-algorand-sdk'}
algod_client = algod.AlgodClient(algod_token="", algod_address=algod_url, headers=headers)

current = 0
end = 10000

while current < end:
    mint_arc_19(algod_client, current)
    current += 1

