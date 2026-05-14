# Models == Database Table
# Ek class == table
'''
URL SHORTNER k liye  chahiye
original URL
short code (jaise abc123)
kitni baar click hua
kab banaya
'''

'''
from .database import Base — dot ka matlab same folder. Base wo cheez hai jisse har model inherit karta hai.
class URL(Base) — ek Python class jo ek database table represent karta hai.
__tablename__ = "urls" — PostgreSQL mein table ka naam ye hoga.
id = Column(Integer, primary_key=True) — har row ka unique number. Auto increment hota hai.
original_url — user ne jo lamba URL diya.
short_code — humara generated chhota code jaise abc123. unique=True matlab do URLs ka same code nahi ho sakta.
clicks — kitni baar us short URL pe click hua. Default 0.
is_active — URL band karna ho toh False kar do, delete nahi karna.
created_at — func.now() automatically current time save karta hai
'''

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from .database import Base

class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key = True , index = True)
    original_url = Column(String, nullable = False)
    short_code = Column(String , unique = True, index = True, nullable = False)
    custom_code = Column(String, nullable = True)  # User-provided custom code
    clicks = Column(Integer, default = 0)
    is_active = Column(Boolean, default = True)
    expires_at = Column(DateTime(timezone = True), nullable = True)  # URL expiry date
    created_at = Column(DateTime(timezone = True), server_default = func.now())
    updated_at = Column(DateTime(timezone = True), server_default = func.now(), onupdate = func.now())


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key = True, index = True)
    url_id = Column(Integer, nullable = False, index = True)  # Reference to URL
    short_code = Column(String, nullable = False, index = True)
    clicks_count = Column(Integer, default = 0)
    unique_visitors = Column(Integer, default = 0)
    timestamp = Column(DateTime(timezone = True), server_default = func.now())
    click_data = Column(JSON, default = {})  # Store hourly/daily click patterns
    referrer_data = Column(JSON, default = {})  # Store referrer sources
    device_data = Column(JSON, default = {})  # Store device types
