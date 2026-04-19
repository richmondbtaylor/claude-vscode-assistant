"""
Local FastAPI server that receives approved LinkedIn DM payloads from n8n
and sends them via Playwright.

Start with:
    uvicorn server:app --port 3001

Then expose publicly with ngrok:
    ngrok http 3001
"""

import os
import hmac
import hashlib
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv
from send_dm import send_linkedin_dm

_executor = ThreadPoolExecutor(max_workers=2)

load_dotenv(dotenv_path=Path.home() / ".claude" / "security" / "linkedin-dm-assistant.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Optional shared secret between n8n and this server for basic security
SERVER_SECRET = os.getenv("SERVER_SECRET", "")


class SendDMPayload(BaseModel):
    conversation_url: str
    message: str
    sender_name: str = ""
    slack_message_ts: str = ""  # Used to update the Slack message after sending


async def _send_and_log(payload: SendDMPayload):
    logger.info(f"Sending DM to {payload.sender_name} at {payload.conversation_url}")
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _executor, send_linkedin_dm, payload.conversation_url, payload.message
    )
    if result["success"]:
        logger.info(f"DM sent successfully to {payload.sender_name}")
    else:
        logger.error(f"Failed to send DM to {payload.sender_name}: {result['error']}")
    return result


@app.post("/send-dm")
async def send_dm(payload: SendDMPayload, request: Request, background_tasks: BackgroundTasks):
    # Optional: verify shared secret header
    if SERVER_SECRET:
        auth_header = request.headers.get("X-Server-Secret", "")
        if not hmac.compare_digest(auth_header, SERVER_SECRET):
            raise HTTPException(status_code=401, detail="Unauthorized")

    # Run Playwright in the background so we return 200 to n8n immediately
    background_tasks.add_task(_send_and_log, payload)

    return JSONResponse({"status": "queued", "sender": payload.sender_name})


@app.get("/health")
async def health():
    return {"status": "ok"}
