from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import data, forecast, loan, clients, watchlist, graph, health, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: run checks, warm up models
    # await startup_checks()
    yield
    # Shutdown: close connections


app = FastAPI(
    title="NeevFinance API",
    version="1.0",
    description="ML-powered financial intelligence for Indian MSMEs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,     prefix="/api")
app.include_router(data.router,       prefix="/api")
app.include_router(forecast.router,   prefix="/api")
app.include_router(loan.router,       prefix="/api")
app.include_router(clients.router,    prefix="/api")
app.include_router(watchlist.router,  prefix="/api")
app.include_router(graph.router,      prefix="/api")
app.include_router(dashboard.router,  prefix="/api")
