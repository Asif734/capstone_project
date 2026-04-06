
from fastapi import FastAPI 
from app.routes import upload_file, query, authentication
from fastapi.middleware.cors import CORSMiddleware

app= FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bup-chat.vercel.app",
        "http://localhost:3000",
        "http://localhost:3000/",
        "http://localhost:5173",
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
