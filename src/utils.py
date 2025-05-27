import hashlib
import json
import os
import random
import string
import time

import phpserialize
import requests

from src.env import config

cred = config()
key = cred["key"]
salt = cred["salt"]


def decode_bytes(obj):
    if isinstance(obj, bytes):
        return obj.decode("utf-8")
    elif isinstance(obj, dict):
        return {decode_bytes(k): decode_bytes(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(decode_bytes(i) for i in obj)
    else:
        return obj


def decode_verify_payment_response(payment_res: str, txn_id: str) -> dict:
    data = decode_bytes(phpserialize.loads(payment_res, decode_strings=True))

    res = {
        "status": int(data["status"]),
        "message": data["msg"],
        "transaction_details": data["transaction_details"].get(txn_id, {}),
    }
    print("Decoded Response: ", res)
    return res


def format_payment_res(payment_res: dict) -> dict:
    data = {}
    for k, v in payment_res.items():
        data[k] = v[0]

    return data


def generate_txn_id() -> str:
    timestamp = int(time.time() * 1000)
    random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    txn_id = f"TXN_{timestamp}_{random_str}"
    print("TXN_ID: ", txn_id)
    return txn_id


def generate_hash_payment(
    txnid: str,
    amount: str,
    productinfo: str,
    firstname: str,
    email: str,
    udf1: str = "",
    udf2: str = "",
    udf3: str = "",
    udf4: str = "",
    udf5: str = "",
) -> str:
    hash_string = f"{key}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|{udf1}|{udf2}|{udf3}|{udf4}|{udf5}||||||{salt}"
    print(f"Hash String: {hash_string}")
    hash_object = hashlib.sha512(hash_string.encode("utf-8"))
    hash_value = hash_object.hexdigest()
    print(f"Generated Hash for Initiate Payment\n: {hash_value}")
    return hash_value


def generic_hash(var1: str, command: str) -> str:
    hash_string = f"{key}|{command}|{var1}|{salt}"
    hash_object = hashlib.sha512(hash_string.encode("utf-8"))
    hash_value = hash_object.hexdigest()
    print(f"Generated Hash for Verify Payment:\n {hash_value}")
    return hash_value


def verify_payment(txn_id: str):
    command = "verify_payment"
    payload = {
        "key": cred["key"],
        "command": "verify_payment",
        "var1": txn_id,
        "hash": generic_hash(var1=txn_id, command=command),
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post(
        url=cred["payu_url"], data=payload, headers=headers, params={"form": "2"}
    )

    print(res.json())

    # v_res = decode_verify_payment_response(
    #     payment_res=res.text.encode("utf-8"), txn_id=txn_id
    # )

    print("Verify Payment Response:\n", res.json())

    file_path = os.path.join("data/verify_payment", f"{txn_id}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(res.json(), f, indent=2, ensure_ascii=False)

    print("Response Saved")

    return res


def refund(mihpayid: str, txnid: str, amount: str) -> dict:
    command = "cancel_refund_transaction"
    payload = {
        "key": key,
        "command": "cancel_refund_transaction",
        "var1": mihpayid,
        "var2": txnid,
        "var3": amount,
        "hash": generic_hash(var1=mihpayid, command=command),
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post(
        url=cred["payu_url"], data=payload, headers=headers, params={"form": "2"}
    )

    print("Response: ", res.json())

    file_path = os.path.join("data/refund", f"{txnid}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(res.json(), f, indent=2, ensure_ascii=False)

    print("Response Saved")
    return res.json()
