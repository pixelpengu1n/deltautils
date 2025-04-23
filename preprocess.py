from fastapi import APIRouter, HTTPException, Request
import requests
import json

router = APIRouter()

PREPROCESS_API_URL = "https://h0gn7fm71g.execute-api.ap-southeast-2.amazonaws.com/dev/preprocess"

@router.post("/preprocess/")
async def preprocess_json(request: Request):
    try:
        input_data = await request.json()

        # Properly serialize JSON to string using json.dumps
        response = requests.post(
            PREPROCESS_API_URL,
            files={"file": ("input.json", json.dumps(input_data), "application/json")}
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
