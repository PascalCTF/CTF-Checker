from sqlalchemy import Column, Integer, String, LargeBinary, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Status(Base):
    __tablename__ = 'status'
    id = Column(Integer, primary_key=True, autoincrement=True)
    checker = Column(Integer, ForeignKey('checkers.id'), nullable=False)
    uptime = Column(Float, nullable=False) # percentage of tests passed
    date = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f'<Status(checker={self.checker}, uptime={self.uptime}, date={self.date})>'
    
class Checkers(Base):
    __tablename__ = 'checkers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    points = Column(Integer, nullable=False)
    flag = Column(String(50), unique=True, nullable=False)
    checker = Column(LargeBinary, nullable=False)

    def __repr__(self):
        return f'<Checkers(name={self.name}, description={self.description}, category={self.category}, points={self.points}, flag={self.flag})>'