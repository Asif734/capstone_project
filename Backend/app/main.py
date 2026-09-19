import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.routes import upload_file, query, authentication, admin
from app.db import sqldb
from app.core.config import settings
from app.db.database import ensure_schema_migrations, initialize_authorized_users, get_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_startup()
    sqldb.Base.metadata.create_all(bind=sqldb.engine)
    db: Session = next(get_db())
    try:
        ensure_schema_migrations(db)
        if settings.SEED_LOCAL_DATA:
            initialize_authorized_users(db)
            from app.db.database import populate_student_data_from_json
            populate_student_data_from_json(db)
    finally:
        db.close()
    yield
app = FastAPI(
    title="BUP Student Assistant API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get_root():
    return {"service": "BUP Student Assistant API", "status": "ok"}


@app.get("/health", tags=["Operations"])
def health_check():
    try:
        with sqldb.engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except Exception:
        logger.exception("Database health check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "unavailable"},
        )
    return {"status": "ok", "database": "available"}

app.include_router(authentication.router, tags=["Authentication"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(upload_file.router, tags=["Upload file"])
app.include_router(query.router, tags=["Query"])
