import json
import os
from urllib.parse import parse_qs

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from src.utils import (
    config,
    format_payment_res,
    generate_hash_payment,
    generate_txn_id,
    verify_payment,
)

cred = config()

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PaymentRequest(BaseModel):
    amount: str
    full_name: str
    email: str
    phone: str
    product_info: str


@app.post("/initiate_payment")
def initiate_payment(request: PaymentRequest):
    txn_id = generate_txn_id()
    _hash = generate_hash_payment(
        amount=request.amount,
        txnid=txn_id,
        email=request.email,
        productinfo=request.product_info,
        firstname=request.full_name,
    )
    redirect_url = "http://localhost:8000/verify_payment"
    payment_data = {
        "key": cred["key"],
        "hash": _hash,
        "txnid": txn_id,
        "amount": request.amount,
        "firstname": request.full_name,
        "email": request.email,
        "phone": request.phone,
        "productinfo": request.product_info,
        "surl": redirect_url,
        "furl": redirect_url,
        "action_url": cred["action_url"],
        "method": "post",
    }

    print("PAYMENT DATA: ", payment_data)

    return {"status": 200, "data": payment_data}


@app.post("/verify_payment")
async def payment_status(request: Request):
    raw = await request.body()
    decoded = raw.decode("utf-8")
    data = format_payment_res(parse_qs(decoded, keep_blank_values=True))
    txn_id = data["txnid"]

    file_path = os.path.join("data/payment", f"{txn_id}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Response from Payment Gateway:\n", data)
    verify_payment(txn_id=txn_id)
    if data["status"] == "success":
        return RedirectResponse(
            url="http://localhost:5173/success", status_code=status.HTTP_303_SEE_OTHER
        )
    return RedirectResponse(
        url="http://localhost:5173/failure", status_code=status.HTTP_303_SEE_OTHER
    )


"""
a:3:{s:6:"status";i:1;s:3:"msg";s:44:"1 out of 1 Transactions Fetched Successfully";s:19:"transaction_details";a:1:{s:24:"TXN_1747374126877_KQ46LH";a:35:{s:8:"mihpayid";s:18:"403993715533930083";s:10:"request_id";s:0:"";s:12:"bank_ref_num";s:18:"899565009864366100";s:3:"amt";s:4:"1.00";s:18:"transaction_amount";s:4:"1.00";s:5:"txnid";s:24:"TXN_1747374126877_KQ46LH";s:18:"additional_charges";s:4:"0.00";s:11:"productinfo";s:12:"Test Payment";s:9:"firstname";s:16:"DebjyotiBanerjee";s:8:"bankcode";s:2:"CC";s:4:"udf1";s:0:"";s:4:"udf2";s:0:"";s:4:"udf3";s:0:"";s:4:"udf4";s:0:"";s:4:"udf5";s:0:"";s:6:"field2";s:6:"398494";s:6:"field9";s:25:"Transaction is Successful";s:10:"error_code";s:4:"E000";s:7:"addedon";s:19:"2025-05-16 11:12:39";s:14:"payment_source";s:4:"payu";s:9:"card_type";s:4:"MAST";s:13:"error_Message";s:8:"NO ERROR";s:16:"net_amount_debit";d:1;s:4:"disc";s:4:"0.00";s:4:"mode";s:2:"CC";s:7:"PG_TYPE";s:5:"CC-PG";s:7:"card_no";s:16:"XXXXXXXXXXXX2346";s:6:"status";s:7:"success";s:14:"unmappedstatus";s:8:"captured";s:12:"Merchant_UTR";N;s:10:"Settled_At";s:19:"0000-00-00 00:00:00_UTR";N_UTR";N;s:10:"Settled_At";s:19:"0000-00-00 00:00:00";s:12:"name_on_card";N;s:10:"card_token";N;s:18:"payment_aggregator";s:4:"PayU";s:12:"offerAvailed";N;}}}
"""
