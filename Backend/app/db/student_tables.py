from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.sqldb import Base, engine


class AuthorizedUser(Base):
    __tablename__ = "authorized_users"

    id = Column(Integer, primary_key=True, index=True)
    reg_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    academic = relationship(
        "AcademicRecord",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    financial = relationship(
        "FinancialRecord",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    reg_id = Column(
        String,
        ForeignKey("authorized_users.reg_id", ondelete="CASCADE"),
        primary_key=True
    )

    semester = Column(String, nullable=False)
    cgpa = Column(Float, nullable=False)
    credits_completed = Column(Integer)

    user = relationship("AuthorizedUser", back_populates="academic")


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    reg_id = Column(
        String,
        ForeignKey("authorized_users.reg_id", ondelete="CASCADE"),
        primary_key=True
    )

    tuition_fee = Column(Integer)
    paid_amount = Column(Integer)
    due_amount = Column(Integer)

    user = relationship("AuthorizedUser", back_populates="financial")


class User(Base):
    __tablename__="users"

    id= Column(Integer, primary_key= True, index= True)
    reg_id= Column(String, unique= True, nullable= False, index= True)
    password_hash= Column(String, nullable= False)



class OTP(Base):
    __tablename__="otps"

    id= Column(Integer, primary_key=True)
    reg_id=Column(String, unique=True, nullable= False, index= True)
    otp= Column(String, nullable= False)

Base.metadata.create_all(bind=engine)
