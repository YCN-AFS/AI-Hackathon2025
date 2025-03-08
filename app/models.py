from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    fullName: str
    accountNumber: str
    bankName: str

class Transaction(BaseModel):
    sender: User
    receiver: User
    amount: float
    currency: str
    fee: float
    note: Optional[str] = None
    paymentMethod: str
    timestamp: Optional[datetime] = None 