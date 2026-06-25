from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().parents[2] / "student_db.db"
DATABASE_URL= f"sqlite:///{DATABASE_PATH}"

engine= create_engine(DATABASE_URL, echo= True)
SessionLocal= sessionmaker(bind= engine)
Base= declarative_base()
