from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import (
    auth,
    data,
    forecast,
    loan,
    clients,
    watchlist,
    graph,
    health,
    dashboard,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: automatically create tables in database
    from backend.database import engine
    from backend.database import Base
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE entities ADD COLUMN IF NOT EXISTS gstin VARCHAR(15)"))
    yield
    # Shutdown: close connections



app = FastAPI(
    title="Finemonix API",
    version="1.0",
    description="ML-powered financial intelligence platform for Indian MSMEs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All routers mounted under /api
app.include_router(auth.router,      prefix="/api")
app.include_router(health.router,    prefix="/api")
app.include_router(data.router,      prefix="/api")
app.include_router(forecast.router,  prefix="/api")
app.include_router(loan.router,      prefix="/api")
app.include_router(clients.router,   prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(graph.router,     prefix="/api")
app.include_router(dashboard.router, prefix="/api")
