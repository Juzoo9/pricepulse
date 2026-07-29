from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from .queue_manager import QueueManager

app = FastAPI(title="PricePulse Browser Proxy")
qm = QueueManager()


class ResultPayload(BaseModel):
    url: str
    html: str


@app.post("/load")
async def load_url(url: str, timeout: float = 45.0):
    result = await qm.submit(url, timeout)
    if result["status"] == "ok":
        return {"status": "success", "html": result["html"]}
    raise HTTPException(status_code=408, detail=result.get("detail", "timeout"))


@app.get("/task")
async def get_task():
    task = await qm.get_task()
    if not task:
        raise HTTPException(status_code=204, detail="No tasks")
    return task


@app.post("/result")
async def set_result(data: ResultPayload):
    await qm.set_result(data.url, data.html)
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok", "pending": len(qm.pending), "processing": len(qm.processing)}