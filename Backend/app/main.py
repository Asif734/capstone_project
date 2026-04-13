
from fastapi import FastAPI 
from app.routes import upload_file, query, authentication
from fastapi.middleware.cors import CORSMiddleware
from app.db import sqldb
from app.db.database import initialize_authorized_users, get_db
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db: Session = next(get_db())
    try:
        initialize_authorized_users(db)
        # Populate student data from private.json
        from app.db.database import populate_student_data_from_json
        populate_student_data_from_json(db)
    finally:
        db.close()
    yield
    # Shutdown

app= FastAPI(lifespan=lifespan)

# Create tables
sqldb.Base.metadata.create_all(bind=sqldb.engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bup-chat.vercel.app",
        "http://localhost:3000",
        "http://localhost:3000/",
        "http://localhost:5173",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#---------#
@app.get("/")
async def get_root():
    return "Server started Successfully"

app.include_router(authentication.router, tags=["Authentication"])
app.include_router(upload_file.router, tags=["Upload file"])
app.include_router(query.router, tags=["Query"])
