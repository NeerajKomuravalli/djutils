from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy import Column, Integer, String, Float, Date, ARRAY
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.future import select
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
    length: Optional[str] = None
    genre: Optional[str] = None
    key: Optional[str] = None
    bpm: Optional[float] = None
    comment: Optional[str] = None
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
    length = Column(String, nullable=True)
    genre = Column(String, index=True, nullable=True)
    key = Column(String, nullable=True)
    bpm = Column(Float, nullable=True)
    comment = Column(String, nullable=True)
    tags = Column(ARRAY(String), nullable=True)

    artists = Column(ARRAY(Integer), nullable=True)

class Artist(BaseModel):
    name: str
    url: str
    platform_id: Optional[int] = None

class ArtistResp(BaseModel):
    id: int
    name: str
    url: str
    platform_id: int

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

class Url(BaseModel):
    url: str

class Platform(BaseModel):
    name: str

class PlatformResp(BaseModel):
    id: int
    name: str

class PlatformDB(Base):
    __tablename__ = "platform"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)

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

def get_platform_name(url:str) -> str:
    if "beatport" in url:
        return "beatport"
    elif "traxsource" in url:
        return "traxsource"
    elif "soundcloud" in url:
        return "soundcloud"
    elif "bandcamp" in url:
        return "bandcamp"

    return ""

@app.put("/addArtist")
async def add_artist(artist: Artist, session: AsyncSession = Depends(get_session)) -> ArtistResp:
        
    
    async with session.begin():
        # Check if the artist already exists with the same name and platform_id
        result = await session.execute(
            select(ArtistDB).filter_by(name=artist.name, platform_id=artist.platform_id)
        )
        existing_artist = result.scalars().first()

        if existing_artist:
            return ArtistResp(
                id=existing_artist.id,
                name=existing_artist.name,
                url=existing_artist.url
            )

        # If the artist doesn't exist, add them to the database
        new_artist = ArtistDB(**artist.model_dump())
        session.add(new_artist)
        await session.flush()
        artists_resp = ArtistResp(
            id=new_artist.id,
            name=new_artist.name,
            url=new_artist.url,
            platform_id=new_artist.platform_id
        )
        await session.commit()
        # Return the newly added artist's ID
        return artists_resp

@app.put("/addPlatform")
async def add_platform(url: Url, session: AsyncSession = Depends(get_session)) -> PlatformResp:
    async with session.begin():
        platform_name = get_platform_name(url.url)
        if platform_name == "":
            # Write code to send approprite message that this platform is not added.
            raise HTTPException(status_code=400, detail="Invalid URL format. Platform name not found.")

        # Call addPlatform endpoint
        platform = Platform(name=platform_name)
        # Check if the platform already exists
        result = await session.execute(
            select(PlatformDB).filter_by(name=platform.name)
        )
        existing_platform = result.scalars().first()
        if existing_platform:
            return PlatformResp(
                id=existing_platform.id,
                name=existing_platform.name
            )

        # If it doesn't exist, add it
        new_platform = PlatformDB(**platform.model_dump())
        session.add(new_platform)
        await session.flush()
        platform_resp = PlatformResp(
            id=new_platform.id,
            name=new_platform.name
        )
        await session.commit()
        
        return platform_resp
