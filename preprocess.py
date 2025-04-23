from fastapi import APIRouter, HTTPException, Request
import requests

router = APIRouter()

# External preprocessing API
PREPROCESS_API_URL = "https://h0gn7fm71g.execute-api.ap-southeast-2.amazonaws.com/dev/preprocess"

@router.post("/preprocess/")
async def preprocess_json(request: Request):
    try:
        # Parse raw JSON input
        input_data = await request.json()

        # Send it to external API as a file-like object using 'files' param
        response = requests.post(
            PREPROCESS_API_URL,
            files={"file": ("input.json", str(input_data).replace("'", '"'), "application/json")}
        )

        # Forward the processed data or error message
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
