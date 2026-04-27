'''
Pehle samajh — routes.py mein actual API endpoints hote hain.
URL shortener mein kya kya chahiye soch:

POST /shorten — long URL bhejo, short code milega
GET /{short_code} — short code bhejo, original URL pe redirect ho
GET /stats/{short_code} — clicks aur details dekho
'''

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from . import models, schemas, services
from .database import get_db

router = APIRouter()

#1.Short URL banai

@router.post("/shorten",response_model = schemas.URLResponse)
def shorten_url(url_data : schemas.URLCreate, db:Session = Depends(get_db)):
    return services.create_short_url(db = db , url_data = url_data)

#2. Short URL per redirect kero
@router.get("/{short_code}")
def redirect_url(short_code : str, db: Session = Depends(get_db)):
    url = services.get_url_by_code(db =db, short_code = short_code)
    if not url:
        raise HTTPException(status_code = 404 , detail = "URL not found")
    services.increment_clicks(db=db , url = url)
    return RedirectResponse(url =url.original_url)

#3. Stats dekho
@router.get("/stats/{short_code}")
def get_stats(short_code : str, db: Session = Depends(get_db)):
    url = services.get_url_by_code(db =db, short_code = short_code)
    if not url:
        raise HTTPException(status_code = 404 , detail = "URL not found")
    return url

'''
Line by line samajh:
APIRouter() — ye FastAPI ka router hai. main.py mein include karenge — wahan sab routes jud jaate hain.

@router.post("/shorten", response_model=schemas.URLResponse)
@router.post — POST request handle karta hai.
"/shorten" — ye URL path hai.
response_model — FastAPI automatically response ko is schema mein convert karega.

def shorten_url(url_data: schemas.URLCreate, db: Session = Depends(get_db)):
url_data: schemas.URLCreate — user ne jo JSON bheja wo yahan aata hai automatically.
db: Session = Depends(get_db) — ye magic hai FastAPI ka. Depends matlab "pehle get_db chalao, jo mile wo db mein daalo." Tu manually database connection nahi banana — FastAPI karta hai.

@router.get("/{short_code}")
{short_code} — path parameter hai. User /abc123 hit kare toh abc123 automatically short_code variable mein aa jaata hai.
RedirectResponse — user ko original URL pe bhej deta hai. Browser automatically redirect ho jaata hai.

raise HTTPException(status_code=404, detail="URL not found")
Agar URL mila nahi toh error do. raise se FastAPI samajhta hai kuch galat hua — automatically error response bhejta hai.

Flow ek baar dekh:
User POST /shorten bhejta hai
    ↓
FastAPI url_data aur db inject karta hai
    ↓
services.create_short_url chalta hai
    ↓
URLResponse wapas jaata hai user ko

User GET /abc123 hit karta hai
    ↓
FastAPI short_code = "abc123" pakadta hai
    ↓
Database mein dhundha
    ↓
Clicks badhaye
    ↓
Original URL pe redirect

'''


