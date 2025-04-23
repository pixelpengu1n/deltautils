from fastapi import APIRouter, HTTPException, Request
import requests
import json

router = APIRouter()

# AWS API Gateway Endpoints
PREPROCESS_URL = "https://h0gn7fm71g.execute-api.ap-southeast-2.amazonaws.com/dev/preprocess"
ANALYSE_URL = "https://h0gn7fm71g.execute-api.ap-southeast-2.amazonaws.com/dev/analyse"

@router.post("/pipeline/")
async def preprocess_and_analyse(request: Request):
    try:
        # Step 0: Receive raw input JSON
        raw_data = await request.json()

        # Step 1: Preprocess
        preprocess_response = requests.post(
            PREPROCESS_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(raw_data)
        )

        if preprocess_response.status_code != 200:
            raise HTTPException(
                status_code=preprocess_response.status_code,
                detail=f"Preprocessing failed: {preprocess_response.text}"
            )

        preprocessed_data = preprocess_response.json()

        # Step 2: Analyse
        analyse_response = requests.post(
            ANALYSE_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(preprocessed_data)
        )

        if analyse_response.status_code != 200:
            raise HTTPException(
                status_code=analyse_response.status_code,
                detail=f"Analysis failed: {analyse_response.text}"
            )

        analysed_data = analyse_response.json()
        return analysed_data

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON input.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
