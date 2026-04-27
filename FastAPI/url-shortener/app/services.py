'''
routes.py — sirf request lo, response do. Koi logic nahi.

services.py — asli kaam yahan. Short code generate karna, 
URL save karna, clicks count karna — sab yahan.

Route  →  Service  →  Database
(request)  (logic)   (data)
'''

import random
import string
from sqlalchemy.orm import Session
# Tune upar import kiya — models poora file hai.
# models.URL matlab — models.py file ke andar URL class.
# Dot ka matlab — is file ke andar ja aur ye cheez le.
from . import models, schemas

def generate_short_code(length = 6): #default value is 6
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters , k = length))

def create_short_url(db:Session, url_data: schemas.URLCreate):
    #unique code generate karo
    while True:
        short_code = generate_short_code()
        #check karo pehle ye code exist to nhi kerta
         #db.query(models.URL)
         #db.query(models.URL)  → URLs table mein ja
         # .filter(...)          → condition lagao
         # .first()              → pehla result lo
        #  SQL mein ye hota:
        #  SELECT * FROM urls WHERE short_code = 'abc123' LIMIT 1;
        
        
        existing = db.query(models.URL).filter(
            models.URL.short_code == short_code).first()

        if not existing:
            break

    #Database main save kero
    db_url = models.URL(
        original_url = str(url_data.original_url),
        short_code = short_code
    )

    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url

def get_url_by_code(db:Session, short_code : str):
    return db.query(models.URL).filter(
        models.URL.short_code == short_code,
        models.URL.is_active == True
    ).first()

def increment_clicks(db:Session, url: models.URL):
    url.clicks += 1
    db.commit()
    db.refresh(url)
    return url




'''
Line by line samajh:
generate_short_code — ascii_letters matlab a-z, A-Z. digits matlab 0-9. 
random.choices 6 random characters pick karta hai. join se string banta hai.

while True — loop isliye kyunki agar generated code pehle se exist kare toh naya banao. 
Collision handle karna zaroori hai.

db.add → db.commit → db.refresh — ye teen steps hamesha saath aate hain.
 Add karo, save karo, latest data wapas lo.

get_url_by_code — is_active == True filter isliye ki band URLs pe redirect na ho.
increment_clicks — har redirect pe clicks +1 hoga.
'''

'''
Function 1:
def generate_short_code(length=6):
Sirf ek parameter — length=6
length — kitne characters ka code banana hai. =6 matlab default value — agar tu kuch na de toh 6 leta hai automatically.
pythongenerate_short_code()    # 6 characters
generate_short_code(8)   # 8 characters


Function 2:
pythondef create_short_url(db: Session, url_data: schemas.URLCreate):
db: Session — database connection chahiye. Bina iske database mein save kaise karenge? Route se aata hai via get_db().
url_data: schemas.URLCreate — user ne jo URL bheja wo yahan aata hai. URLCreate schema yaad hai? Usme original_url tha — wahi yahan milta hai url_data.original_url se.

Function 3:
pythondef get_url_by_code(db: Session, short_code: str):
db: Session — database mein dhundhna hai toh connection chahiye.
short_code: str — kaunsa code dhundhna hai? User ne /abc123 hit kiya toh abc123 yahan aayega.

Function 4:
pythondef increment_clicks(db: Session, url: models.URL):
db: Session — clicks save karne ke liye connection chahiye.
url: models.URL — pehle se mila hua URL object. Naya dhundhne ki zaroorat nahi — pehle get_url_by_code se mila, wahi yahan pass kiya.

Ek pattern notice kar:
db: Session    →  hamesha jab database se kaam ho
str, int       →  simple values jab user se aaye
schemas.X      →  jab poora request object aaye
models.X       →  jab database object aaye

Flow samajh:
User request aai
    ↓
Route ne pakdi
    ↓
Service ko di (db + data)
    ↓
Service ne database se kaam kiya
    ↓
Result wapas route ko
    ↓
User ko response
'''