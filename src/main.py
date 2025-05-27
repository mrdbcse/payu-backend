import json
import os
from urllib.parse import parse_qs

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from src.env import ENV
from src.utils import (
    config,
    format_payment_res,
    generate_hash_payment,
    generate_txn_id,
    refund,
    refund_status,
    verify_payment,
)

cred = config(env=ENV)

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


class RefundRequest(BaseModel):
    mihpayid: str
    txnid: str
    amount: str


class RefundStatusRequest(BaseModel):
    request_id: str


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


@app.post("/initiate_refund")
async def initiate_refund(request: RefundRequest):
    res = refund(amount=request.amount, mihpayid=request.mihpayid, txnid=request.txnid)
    print("Refund Response:\n", res)
    return {"status": 200, "data": res}


@app.post("/check_refund_status")
async def check_refund_status(request: RefundStatusRequest):
    res = refund_status(request_id=request.request_id)
    print("Refund Status Response:\n", res)
    return {"status": 200, "data": res}
