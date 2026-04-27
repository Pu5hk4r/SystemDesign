'''
Sql Alchemy is ORM--make python talk to database without use of SQL
CREATE_ENGINE makes data connection
SESSIONMAKER--for every request make a session
BASE-- every model(table) inherit it

COMMANDS
psql -U postgres
<Sql> query
\l list database
\q  quit
netstat -ano | findstr : 5432  port conflict
# Kaun use kar raha hai port ko
netstat -ano | findstr :5432

# PID note karo last column mein, phir:
taskkill /PID 1234 /F
# 1234 ki jagah apna PID
# Sabse pehle check karo PostgreSQL service chal rahi hai ya nahi
Get-Service -Name postgresql*

'''
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm  import  sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()  #take things from env

DATABASE_URL = os.getenv("DATABASE_URL")

'''
Engine = database permanent connection
Session = ek request ka temporary connection — kaam karo, band karo.
'''

engine = create_engine(autocommit = False, autoflush = False, bind = engine)
Base = declarative_base()

#Dependency Injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()