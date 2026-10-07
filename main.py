from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import dashscope
from dashscope import Generation
import logging
import csv
from datetime import datetime
from google.cloud import aiplatform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    logger.error("DASHSCOPE_API_KEY is not set!")
else:
    dashscope.api_key = api_key

@app.get("/")
async def read_index():
    return FileResponse("index.html")

class PromptRequest(BaseModel):
    prompt: str
    model: str = "qwen-max"

class RatingRequest(BaseModel):
    prompt: str
    response: str
    type: str
    score: str

class OptimizeRequest(BaseModel):
    prompt_to_optimize: str
    example_path: str
    project_id: str
    location: str = "us-central1"

@app.post("/generate")
async def generate(request: PromptRequest):
    logger.info(f"Received request for model: {request.model}")
    try:
        response = Generation.call(
            model=request.model,
            messages=[{'role': 'user', 'content': request.prompt}]
        )
        if response.status_code == 200:
            return {"result": response.output.text}
        else:
            raise HTTPException(status_code=500, detail=response.message)
    except Exception as e:
        logger.error(f"Internal Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/rate")
async def rate(request: RatingRequest):
    try:
        with open("feedback.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if f.tell() == 0:
                writer.writerow(["timestamp", "prompt", "response", "type", "score"])
            writer.writerow([datetime.now().isoformat(), request.prompt, request.response, request.type, request.score])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not save rating")

@app.post("/optimize")
async def optimize_prompt(request: OptimizeRequest):
    try:
        aiplatform.init(project=request.project_id, location=request.location)
        logger.info(f"Triggering optimization for prompt on dataset: {request.example_path}")
        
        job = aiplatform.CustomJob(
            display_name=f"prompt-opt-{datetime.now().strftime('%Y%m%d')}",
            worker_pool_specs=[{
                "machine_spec": {"machine_type": "n1-standard-4"},
                "replica_count": 1,
                "container_spec": {
                    "image_uri": "us-docker.pkg.dev/vertex-ai/genai/prompt-optimizer:latest",
                    "args": ["--config_gcs_path=" + request.example_path.replace("feedback.csv", "config.json")]
                }
            }]
        )
        job.run(sync=False)
        logger.info(f"Optimization job triggered: {job.resource_name}")
        return {"status": "triggered", "job_id": job.resource_name}
    except Exception as e:
        logger.error(f"Optimization Job Submission Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
