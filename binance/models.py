from sqlalchemy import ( 
    Column, String, 
    Float, Boolean
)
from utils.db import Base, engine


class BncAlert(Base):
    """send alert if price >= x or <= y"""
    __tablename__ = 'bnc_alerts'
    symbol = Column(String(16), primary_key=True)
    higher = Column(Float)
    lower = Column(Float)
    watch = Column(Boolean)

Base.metadata.create_all(engine)
