from fastapi import FastAPI
from .database import engine, Base
from .routes import router

#Database main table bnao

Base.metadata.create_all(bind = engine)

#FastAPI app bnao

app = FastAPI(title = "URL Shortner")

#Routes include karo

app.include_router(router)


"""
Base.metadata.create_all(bind=engine) — ye automatically tables banata hai PostgreSQL mein. models.py mein jo URL class likhi thi — wahi table ban jaati hai. Manually SQL likhne ki zaroorat nahi.
app = FastAPI(title="URL Shortener") — poori application yahan se shuru hoti hai.
app.include_router(router) — routes.py mein jo bhi endpoints likhe hain sab yahan jud jaate hain.

"""