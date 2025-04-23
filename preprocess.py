import json
from datetime import datetime
import numpy as np

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()

class DataPreprocessor:
    def __init__(self, json_data):
        self.data = self.load_json(json_data)

    def load_json(self, json_data):
        try:
            data = json.loads(json_data)
            return [data] if isinstance(data, dict) else data
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format.")

    def clean_data(self):
        cleaned_datasets = []
        for dataset in self.data:
            dataset.setdefault("events", [])
            cleaned_events = []

            for event in dataset["events"]:
                try:
                    event.setdefault("time_object", {
                        "timestamp": datetime.utcnow().isoformat(),
                        "timezone": "UTC"
                    })

                    # Format timestamp
                    timestamp = event["time_object"].get("timestamp")
                    if isinstance(timestamp, str):
                        event["time_object"]["timestamp"] = self.format_timestamp(timestamp)

                    event.setdefault("attribute", {})
                    event["attribute"] = self.clean_attributes(event["attribute"])

                    cleaned_events.append(event)
                except Exception as e:
                    print(f"Error processing event: {e}")

            if cleaned_events:
                dataset["events"] = cleaned_events
                cleaned_datasets.append(dataset)

        return cleaned_datasets

    @staticmethod
    def format_timestamp(timestamp):
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).isoformat()
        except Exception:
            try:
                return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").isoformat()
            except Exception:
                return str(timestamp)

    @staticmethod
    def clean_attributes(attributes):
        cleaned = {}
        for k, v in attributes.items():
            if v is None or v == "":
                cleaned[k] = None
            elif isinstance(v, dict):
                cleaned[k] = list(v.values())[0] if v else None
            elif isinstance(v, float) and np.isnan(v):
                cleaned[k] = None
            elif isinstance(v, str) and v.replace(".", "", 1).replace("-", "", 1).isdigit():
                try:
                    cleaned[k] = float(v)
                except Exception:
                    cleaned[k] = v
            else:
                cleaned[k] = v
        return cleaned

@router.post("/preprocess/")
async def process_json(file: UploadFile = File(...)):
    try:
        content = await file.read()
        preprocessor = DataPreprocessor(content.decode("utf-8"))
        cleaned = preprocessor.clean_data()

        cleaned = json.loads(json.dumps(cleaned, default=lambda x: None if isinstance(x, float) and np.isnan(x) else x))
        return {"cleaned_data": cleaned}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
