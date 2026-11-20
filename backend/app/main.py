from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db import get_session
from app.models.reference import Examination

from app.api.v1.routes import router as v1

app = FastAPI(title="Maharashtra College Finder API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_methods=["GET", "POST"],
                   allow_headers=["*"])


app.include_router(v1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/exams")
def list_exams(db: Session = Depends(get_session)):
    rows = db.scalars(select(Examination).order_by(Examination.id))
    return [{"code": e.code, "name": e.name, "primary_metric": e.primary_metric, "stream": e.stream} for e in rows]
