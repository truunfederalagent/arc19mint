import pandas as pd
import json
from algosdk.v2client import algod
from algosdk import mnemonic
from algosdk.future.transaction import AssetConfigTxn, AssetDestroyTxn
import requests, hashlib, base64, json
from cid import make_cid
from algosdk.encoding import encode_address

with open('config/secrets.conf') as f:
    secrets = json.loads(f.read())


ipfs_url = 'https://api.nft.storage/upload'
headers = {
    "Authorization": f'Bearer {secrets["ipfs_api_key"]}'
}

pk = mnemonic.to_public_key(secrets['mnemonic'])
sk = mnemonic.to_private_key(secrets['mnemonic'])


def wait_for_confirmation(client, txid, create=True):
    """
    Utility function to wait until the transaction is
    confirmed before proceeding.
    """
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print("Transaction {} confirmed in round {}.".format(txid, txinfo.get('confirmed-round')))
    print(txinfo)
    if create:
        return txinfo['asset-index']
    else:
        return txinfo


def sign_and_send_txn(algod_client, txn, create=True):
    # Sign with secret key of creator
    stxn = txn.sign(sk)
    
    # Send the transaction to the network and retrieve the txid.
    txid = algod_client.send_transaction(stxn)
    print(txid)
    
    # Retrieve the asset ID of the newly created asset by first
    # ensuring that the creation transaction was confirmed,
    # then grabbing the asset id from the transaction.
    
    # Wait for the transaction to be confirmed
    return wait_for_confirmation(algod_client,txid, create)


def mint_arc_19(algod_client, num):
    meta_df = pd.read_csv('MetaDefender_arc69.csv')
    properties = meta_df.iloc[num].to_dict()

    element = properties['Name']
    img_url = f'MetaDefenders/{element.upper()}_BASIC.jpg'

    version, codec, reserve_address = pin_required_data(img_url)
    print(version, codec, reserve_address)

    # Get network params for transactions before every transaction.
    params = algod_client.suggested_params()
    # comment these two lines if you want to use suggested params
    params.fee = 1000
    params.flat_fee = True
    asset_name = f'MetaDefender#{num + 1}'
    unit_name = f'AGMD{num + 1}'
    url = f'template-ipfs://{{ipfscid:{version}:{codec}:reserve:sha2-256}}'
    print(asset_name, unit_name)
    
    meta_data = {
        "description": "Metarilla Defenders are the 4th of 8 Eras of Metarillas on a dangerous journey to Sagittarius A",
        "standard": "arc69",
        "properties": properties
    }

    txn = AssetConfigTxn(
        sender=pk,
        sp=params,
        total=1,
        default_frozen=False,
        unit_name=unit_name,
        asset_name=asset_name, 
        manager=pk,
        reserve=reserve_address,
        freeze=None,
        clawback=None,
        strict_empty_address_check=False,
        url=url,
        note=json.dumps(meta_data).encode(),
        decimals=0)

    return sign_and_send_txn(algod_client, txn)


def update_arc_19(algod_client, num, img_path=None, meta=False):
    meta_df = pd.read_csv('MetaDefender_arc69.csv')
    asset_df = pd.read_csv('reserves.csv')
    properties = meta_df.iloc[num].to_dict()
    asset_info = asset_df.iloc[num].to_dict()

    if img_path:
        version, codec, reserve_address = pin_required_data(img_path)
        print(version, codec, reserve_address)
    else:
        reserve_address = asset_info['reserve']
    
    url = asset_info['url']
    index = asset_info['asset_id']
    asset_name = asset_info['name']
    unit_name = asset_info['unit-name']

    params = algod_client.suggested_params()
    params.fee = 1000
    params.flat_fee = True
    
    meta_data = {
            "description": "Metarilla Defenders are the 4th of 8 Eras of Metarillas on a dangerous journey to Sagittarius A",
            "standard": "arc69",
            "properties": properties
    }

    note = json.dumps(meta_data).encode() if meta else None

    txn = AssetConfigTxn(
        sender=pk,
        sp=params,
        total=1,
        index=index,
        default_frozen=False,
        unit_name=unit_name,
        asset_name=asset_name, 
        manager=pk,
        reserve=reserve_address,
        freeze=None,
        clawback=None,
        strict_empty_address_check=False,
        url=url,
        note=note,
        decimals=0)

    return sign_and_send_txn(algod_client, txn, create=False)


def destroy_asset(algod_client, asset):
    params = algod_client.suggested_params()
    # comment these two lines if you want to use suggested params
    params.fee = 1000
    params.flat_fee = True
    txn = AssetDestroyTxn(
        sender=pk,
        sp=params,
        index=asset)

    return sign_and_send_txn(algod_client, txn)


def pin_required_data(path):
    img_file = open(path, 'rb')
    img_response_data = requests.post(ipfs_url, img_file, headers=headers).json()
    if not img_response_data['ok']:
        return None

    print(img_response_data)

    img_cid = img_response_data['value']['cid']
    print(img_cid)

    ipfs = make_cid(img_cid)
    return (ipfs.version, ipfs.codec, encode_address(ipfs.multihash[2:]))