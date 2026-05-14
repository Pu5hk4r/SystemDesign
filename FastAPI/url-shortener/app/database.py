'''
Sql Alchemy is ORM--make python talk to database without use of SQL
CREATE_ENGINE makes data connection
SESSIONMAKER--for every request make a session
BASE-- every model(table) inherit it

COMMANDS
psql -U postgres
<Sql> query
\ l list database
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
import redis
import logging

load_dotenv()  #take things from env

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

logger = logging.getLogger(__name__)

'''
Engine = database permanent connection
Session = ek request ka temporary connection — kaam karo, band karo.
Redis = in-memory cache for fast access aur rate limiting
'''

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis connection pool for efficiency
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("✓ Redis connected successfully")
except Exception as e:
    logger.warning(f"⚠ Redis connection failed: {e}")
    redis_client = None

#Dependency Injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    """Get Redis client - returns None if not connected"""
    return redis_client