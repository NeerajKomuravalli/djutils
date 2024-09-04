from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy import Column, Integer, String, Float, Date, ARRAY
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from contextlib import asynccontextmanager
from typing import AsyncGenerator

PASSWORD = "SCRAM-SHA-256$4096:JZavfYFOt+UfXDmFS04Kyg==$XN/agqg8VV1Se4+8qbfMiDUvK5bKHFRzkhNcZ487Y90=:znDjm5z80+wrIlHJ4BLmVl0oGb+hDHeWa3g8ZBKelTw="
DATABASE_URL = f"postgresql+asyncpg://djutils_api:{PASSWORD}@localhost/djutils"

# FastAPI App
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://mglabannbfahakibcjfmihokjehehhkb"],  # Allow your extension's origin
    allow_credentials=True,
    allow_methods=["*"],  # Or specify allowed methods, e.g., ["GET", "POST", "PUT"]
    allow_headers=["*"],  # Or specify allowed headers, e.g., ["Content-Type"]
)

# SQLAlchemy Setup
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

# Pydantic Model
class Track(BaseModel):
    title: str
    label: Optional[str] = None
    version: Optional[str] = None
    released: Optional[str] = None  # Use date string format
    genre: Optional[str] = None
    key: Optional[str] = None
    bpm: Optional[float] = None
    comments: Optional[str] = None
    tags: Optional[List[str]] = None
    artists: Optional[List[int]] = None

# SQLAlchemy Model
class TrackDB(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    version = Column(String, index=True, nullable=True)
    label = Column(String, index=True, nullable=True)
    released = Column(String, nullable=True)
    genre = Column(String, index=True, nullable=True)
    key = Column(String, nullable=True)
    bpm = Column(Float, nullable=True)
    comments = Column(String, nullable=True)
    tags = Column(ARRAY(String), nullable=True)

    artists = Column(ARRAY(Integer), nullable=True)

class ArtistDB(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    
    # platform_id as a foreign key referencing PlatformDB
    platform_id = Column(Integer, ForeignKey('platform.id'), nullable=False)
    
    # URL for the artist
    url = Column(String, nullable=False)
    
    # Relationship to the PlatformDB
    platform = relationship("PlatformDB")

class PlatformDB(Base):
    __tablename__ = "platform"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    url = Column(String, nullable=False)

# Create the database tables using a lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

# Dependency for getting the database session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

# PUT endpoint
@app.put("/addTrack")
async def add_track(track: Track, session: AsyncSession = Depends(get_session)):
    async with session.begin():
        # Use model_dump() instead of dict()
        new_track = TrackDB(**track.model_dump())
        session.add(new_track)
    await session.commit()
    return {"message": "Track added successfully"}
