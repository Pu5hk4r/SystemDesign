'''
schemas.py — ye samajh pehle.
Model vs Schema fark:

Model = database table
Schema = API request/response ka format — user kya bhejega, user ko kya milega

Soch — URL shortener mein:
User kya bhejega? → sirf original_url
User ko kya milega? → short_code, original_url, clicks, created_at

Samajh:
URLCreate — user sirf URL bhejega. HttpUrl automatically check karega valid URL hai ya nahi. google nahi chalega, 
https://google.com chalega.

URLResponse — user ko ye sab milega response mein.

class Config: from_attributes = True — ye SQLAlchemy model ko Pydantic schema 
mein convert karne ke liye chahiye. 

Bina iske response nahi banega.

Ek important cheez notice kar:

URLCreate mein HttpUrl hai — strict validation.

URLResponse mein str hai — kyunki database se aata hai toh 
already valid hai, strict validation ki zaroorat nahi.

'''
#HttpUrl — automatically validate karta hai ki valid URL hai ya nahi. Koi random string nahi chalegi.

from pydantic import BaseModel, HttpUrl
from datetime import daytime

#User se input lega -- sirf original URL

class URLCreate(BaseModel):
    original_url : HttpUrl

# User ko response denge -- saari details

class URLResponse(BaseModel):
    id : int
    original_url : str
    short_code : str
    clicks : int
    is_active : bool
    created_at : datetime

    class Config:
        from_attributes = True
