from sqlalchemy import ( 
    Column, Integer, String, 
    Float, DateTime, Text, Index
)
from utils.db import Base, engine


class Token(Base):
    __tablename__ = 'dex_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_address = Column(String(255), unique=True)
    chain_id = Column(String(50))
    url = Column(String(255))
    icon = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime)

    __table_args__ = (
        Index('idx_created_at', 'created_at'),
    )


class TokenDetail(Base):
    __tablename__ = 'dex_token_details'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chain_id = Column(String(50))
    dex_id = Column(String(50))
    url = Column(String(255))
    token_address = Column(String(255))
    pair_address = Column(String(255))
    name = Column(String(255))
    symbol = Column(String(50))
    priceUsd = Column(Float)
    liquidityUsd = Column(Float)
    volume24h = Column(Float)
    priceChange24h = Column(Float)
    market_cap = Column(Float)
    created_at = Column(DateTime)

    __table_args__ = (
        Index('idx_token_address', 'token_address'),
        Index('idx_created_at', 'created_at'),
    )

class Alert(Base):
    __tablename__ = 'dex_alerts'
    token_address = Column(String(255), primary_key=True)
    last_priceUsd = Column(Float)
    last_priceChange24h = Column(Float)
    last_volume24h = Column(Float)
    last_alert_type = Column(String(50))
    last_alert_time = Column(DateTime)
    dex_id = Column(String(50))

# Crate table
Base.metadata.create_all(engine)
