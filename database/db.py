from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class State(Base):
    __tablename__ = 'state'
    id = Column(Integer, primary_key=True)
    last_processed_level = Column(Integer)
    timestamp = Column(Integer)  # Unix timestamp

# table for both successful and missed blocks
class BlockBaking(Base):
    __tablename__ = 'block_baking'
    id = Column(Integer, primary_key=True)
    block_level = Column(Integer, nullable=False)
    delegate = Column(Integer, nullable=False)
    successful = Column(Integer, nullable=False)  # 1 for success, 0 for missed
    alerted = Column(Integer, nullable=False, default=0)  # 1 if alert sent, 0 otherwise
    recovered = Column(Integer, nullable=False, default=0)  # 1 if recovery alert sent, 0 otherwise

# table for both successful and missed attestations
class BlockAttestation(Base):
    __tablename__ = 'block_attestation'
    id = Column(Integer, primary_key=True)
    block_level = Column(Integer, nullable=False)
    delegate = Column(Integer, nullable=False)
    successful = Column(Integer, nullable=False)  # 1 for success, 0 for missed
    alerted = Column(Integer, nullable=False, default=0)  # 1 if alert sent, 0 otherwise

def get_engine(db_url):
    return create_engine(db_url)

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

def init_db(engine):
    Base.metadata.create_all(engine)
