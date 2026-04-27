'''
Pehle samajh — routes.py mein actual API endpoints hote hain.
URL shortener mein kya kya chahiye soch:

POST /shorten — long URL bhejo, short code milega
GET /{short_code} — short code bhejo, original URL pe redirect ho
GET /stats/{short_code} — clicks aur details dekho
'''

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db
import random
import string #random aur string kyun?Short code generate karne ke liye — abc123 jaisa. Khud sochna hoga logic.

