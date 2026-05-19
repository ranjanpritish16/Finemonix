from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import (
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
    # Startup: run DB checks, warm up models, etc.
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
    allow_origins=["http://localhost:3000"],   # Next.js dev origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All routers mounted under /api
app.include_router(health.router,    prefix="/api")
app.include_router(data.router,      prefix="/api")
app.include_router(forecast.router,  prefix="/api")
app.include_router(loan.router,      prefix="/api")
app.include_router(clients.router,   prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(graph.router,     prefix="/api")
app.include_router(dashboard.router, prefix="/api")
