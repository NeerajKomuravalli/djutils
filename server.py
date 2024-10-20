import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator, field_validator
from sqlalchemy import Column, Integer, String, ForeignKey, update, Float, ARRAY
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.future import select
from sqlalchemy import update
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from rapidfuzz import fuzz

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
    url: str
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

    @field_validator('bpm', mode="before")
    def convert_bpm(cls, value):
        if isinstance(value, str):  # Check if the value is a string
            try:
                return int(value)  # Convert the string to an integer
            except ValueError:
                raise ValueError("bpm must be a valid integer")
        return value  # If it's already an integer, return it unchanged

    
class TrackResp(Track):
    id: int

    model_config = {
        'from_attributes': True
    }

class SimilarTrackResp(Track):
    score: float

    model_config = {
        'from_attributes': True
    }

class TrackRespList(BaseModel):
    data: List[TrackResp] = []

# SQLAlchemy Model
class TrackDB(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    url = Column(String)
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

    @field_validator('platform_id', mode="before")
    def convert_bpm(cls, value):
        if isinstance(value, str):  # Check if the value is a string
            try:
                return int(value)  # Convert the string to an integer
            except ValueError:
                raise ValueError("platform_id must be a valid integer")
        return value  # If it's already an integer, return it unchanged
    

class ArtistResp(Artist):
    id: int

    model_config = {
        'from_attributes': True
    }

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

class Id(BaseModel):
    id: int

class Platform(BaseModel):
    name: str

class PlatformResp(Platform):
    id: int

    model_config = {
        'from_attributes': True
    }

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

async def _add_track(track:Track, session: AsyncSession) -> TrackResp:
    new_track = TrackDB(**track.model_dump())
    session.add(new_track)
    await session.flush()
    new_track_resp = TrackResp.model_validate(new_track)
    await session.commit()

    return new_track_resp

def match_artists(artist_name: str, artist_db_names: List[str]) -> float:
    """
    Match the artist name with the artist names in the database and return the best score.
    """
    max_score = 0
    for db_name in artist_db_names:
        # Use fuzzy matching to compare the artist's name
        score = fuzz.partial_ratio(artist_name.lower(), db_name.lower())
        max_score = max(max_score, score)
    return max_score

@app.get("/similarTracks", response_model=List[SimilarTrackResp])
async def get_similar_tracks(track: str = Query(...), artists:str=Query(...), session: AsyncSession = Depends(get_session)):
# async def get_similar_tracks(track: Track, artists: List[Artist], session: AsyncSession = Depends(get_session)):
    # Filter TrackDb for similar name as track.title
    # If no tracks are found then no similar tracks exist. Return
    # If tarcks exists then iterate over them and:
    # Find fuzzy match score for titles
    # Find artist name match score by:
        # split the artists name into words and then do a fuzzy match 
        # logic to only take theb score with max score and then average it
    # If both title and artists name score matches then do a comparison 
    # of each parameter and then return a score along with track

    # Step 1: Filter TrackDB for similar name as track.title

    track: Track = Track.model_validate_json(track)
    artists_list = json.loads(artists)
    artists: List[Artist] = [Artist(**artist) for artist in artists_list]
    # stmt = select(TrackDB).filter(TrackDB.title.ilike(f"%{track.title}%"))
    stmt = select(TrackDB).filter(
        TrackDB.title.ilike(f"%{track.title}%"),
        TrackDB.url != track.url  # Exclude the track with the same URL
    )
    result = await session.execute(stmt)
    tracks_in_db = result.scalars().all()

    if not tracks_in_db:
        # No similar tracks found, return an empty list
        return []

    # Step 2: Iterate over found tracks and calculate scores
    similar_tracks = []
    for track_db in tracks_in_db:
        # Fuzzy match score for track titles
        title_score = fuzz.ratio(track.title.lower(), track_db.title.lower())

        # Step 3: Find matching artist scores for each track in DB
        # Get artists from the database for this track
        artist_stmt = select(ArtistDB).filter(ArtistDB.id.in_(track_db.artists))
        artist_result = await session.execute(artist_stmt)
        db_artists = artist_result.scalars().all()

        # Get the names of the artists for the track in DB
        db_artist_names = [db_artist.name for db_artist in db_artists]
        db_artist_names_str = " ".join(db_artist_names)
        
        # Get the names of the tracks from the source list of Artists
        db_artist_names_str_src = " ".join([db_artist.name for db_artist in artists])
        artist_score = fuzz.token_sort_ratio(
            db_artist_names_str, 
            db_artist_names_str_src,
        )

        version_score = fuzz.partial_token_sort_ratio(
            track_db.version, 
            track.version,
        )

        label_score = fuzz.ratio(track_db.label, track.label)

        genre_score = fuzz.ratio(track_db.genre, track.genre)

        key_score = fuzz.ratio(track_db.key, track.key)

        if track_db.bpm != track.bpm:
            bpm_score = 0
        else:
            bpm_score = 1

        similarity_score = (title_score + artist_score + version_score + label_score + genre_score + key_score + bpm_score)/7

        # Step 5: Add the track and its score to the result
        similar_tracks.append(
            SimilarTrackResp(
                **track_db.__dict__, 
                score=similarity_score,
        ))

    return similar_tracks

# PUT endpoint
@app.put("/addTrack")
async def add_track(track: Track, session: AsyncSession = Depends(get_session)) -> TrackResp:
    async with session.begin():
        try:
            track_data_list = await _get_tracks(track.url, session)
            if len(track_data_list.data) > 1:
                raise Exception("More than one tracks found!")
            elif len(track_data_list.data) == 1:
                track_data = track_data_list.data[0]
                # Update the track data in postgres with the latest track data
                await session.execute(
                    update(TrackDB)
                    .where(TrackDB.id == track_data.id)
                    .values(
                        title=track.title,
                        artists=track.artists,
                        url=track.url,
                        version=track.version,
                        label=track.label,
                        released=track.released,
                        length=track.length,
                        genre=track.genre,
                        key=track.key,
                        bpm=track.bpm,
                        comment=track.comment,
                        tags=track.tags
                    )
                )
                await session.commit()
            else:
                # If no track data found, add the new track
                track_data = await _add_track(track, session)

        except HTTPException as e:
            if e.status_code == 404:
                track_data = await _add_track(track, session)
            else:
                raise Exception(e)
        except Exception as e:
            raise Exception(e)
        
        return track_data

async def _get_tracks(url:str, session: AsyncSession) -> TrackRespList:
    # Build a dynamic query using the track attributes provided in the request
    query = select(TrackDB)

    # Add filters for each non-null attribute in the Track model
    if url:
        query = query.filter(TrackDB.url == url)

    # Execute the query
    result = await session.execute(query)
    track_data = result.scalars().all()

    # Check if track exists
    if not track_data:
        raise HTTPException(status_code=404, detail="Track not found")

    tracks_resp = TrackRespList(
        data = []
    )

    for track in track_data:
        tracks_resp.data.append(TrackResp.model_validate(track))

    return tracks_resp

@app.get("/getTrack", response_model=TrackResp)
async def get_track(url: str, session: AsyncSession = Depends(get_session)) -> TrackResp:
    async with session.begin():
        track_data_list = await _get_tracks(url, session)
        if len(track_data_list.data) > 1:
            raise Exception("More than one tracks found!")
        elif len(track_data_list.data) == 1:
            return track_data_list.data[0]
        else:
            return None

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
        artists_resp = ArtistResp.model_validate(new_artist)
        await session.commit()
        # Return the newly added artist's ID
        return artists_resp

@app.get("/getArtist")
async def get_artist(id: int, session: AsyncSession = Depends(get_session)) -> ArtistResp:
    async with session.begin():
        # Build a dynamic query using the track attributes provided in the request
        query = select(ArtistDB)

        query = query.filter(ArtistDB.id == id)

        # Execute the query
        result = await session.execute(query)
        artist_data = result.scalars().first()

        # Check if track exists
        if not artist_data:
            raise HTTPException(status_code=404, detail="Artist not found")

        return ArtistResp.model_validate(artist_data)

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
        platform_resp = PlatformResp.model_validate(new_platform)
        await session.commit()
        
        return platform_resp
