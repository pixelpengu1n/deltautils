import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

class DataAnalyser:
    def __init__(self, json_data):
        self.data = json_data
        self.records = self.convert_to_records()
        self.dataset_categories = self.get_dataset_categories()

    def convert_to_records(self):
        records = []
        for dataset in self.data.get("cleaned_data", []):
            for event in dataset.get("events", []):
                row = {
                    "dataset_id": dataset.get("dataset_id", "Unknown"),
                    "dataset_type": dataset.get("dataset_type", "Unknown"),
                    "event_type": event.get("event_type", "Unknown"),
                    "timestamp": event.get("time_object", {}).get("timestamp", None),
                }

                attributes = event.get("attribute", {})
                row.update(attributes)
                records.append(row)

        for record in records:
            if record["timestamp"]:
                try:
                    record["timestamp"] = datetime.fromisoformat(record["timestamp"])
                except ValueError:
                    record["timestamp"] = None

        return records

    def get_dataset_categories(self):
        return list(set(record["dataset_type"] for record in self.records))

    def analyze_by_category(self):
        results = {}
        for category in self.dataset_categories:
            category_records = [rec for rec in self.records if rec["dataset_type"] == category]
            results[category] = self.generate_analysis(category_records, category)
        return results

    def generate_analysis(self, records, category):
        insights = {
            "category": category,
            "summary": {},
            "trends": {},
            "correlations": {},
            "distribution": {},
            "patterns": {},
            "anomalies": {},
        }

        numeric_keys = set()
        for record in records:
            for key, value in record.items():
                if isinstance(value, (int, float)):
                    numeric_keys.add(key)

        if numeric_keys:
            insights["summary"]["statistics"] = {}
            for key in numeric_keys:
                values = [rec[key] for rec in records if isinstance(rec.get(key), (int, float))]
                if values:
                    insights["summary"]["statistics"][key] = {
                        "min": min(values),
                        "max": max(values),
                        "mean": sum(values) / len(values),
                        "median": sorted(values)[len(values) // 2],
                        "std_dev": (
                            sum((x - sum(values) / len(values)) ** 2 for x in values) / len(values)
                        ) ** 0.5,
                    }

        insights["trends"] = self.detect_trends(records)
        insights["correlations"] = self.detect_correlations(records, numeric_keys)
        insights["distribution"] = self.detect_distribution(records, numeric_keys)
        insights["patterns"] = self.detect_patterns(records)
        insights["anomalies"] = self.detect_anomalies(records)

        return insights

    def detect_trends(self, records):
        trends = {}
        timestamps = [rec["timestamp"] for rec in records if rec["timestamp"]]
        timestamps.sort()
        if timestamps:
            trends["first_event"] = timestamps[0].isoformat()
            trends["last_event"] = timestamps[-1].isoformat()
            trends["event_count"] = len(timestamps)
        return trends

    def detect_correlations(self, records, numeric_keys):
        correlations = {}
        for key1 in numeric_keys:
            for key2 in numeric_keys:
                if key1 != key2:
                    values1 = [rec[key1] for rec in records if isinstance(rec.get(key1), (int, float))]
                    values2 = [rec[key2] for rec in records if isinstance(rec.get(key2), (int, float))]
                    if len(values1) == len(values2) and len(values1) > 5:
                        correlation = sum(a * b for a, b in zip(values1, values2)) / len(values1)
                        correlations[f"{key1}-{key2}"] = correlation
        return correlations

    def detect_distribution(self, records, numeric_keys):
        distribution = {}
        for key in numeric_keys:
            values = [rec[key] for rec in records if isinstance(rec.get(key), (int, float))]
            if values:
                values_sorted = sorted(values)
                distribution[key] = {
                    "min": min(values_sorted),
                    "max": max(values_sorted),
                    "quartiles": {
                        "Q1": values_sorted[len(values_sorted) // 4],
                        "Q2": values_sorted[len(values_sorted) // 2],
                        "Q3": values_sorted[(3 * len(values_sorted)) // 4],
                    },
                }
        return distribution

    def detect_patterns(self, records):
        patterns = {}
        numeric_keys = set()
        for record in records:
            for key, value in record.items():
                if isinstance(value, (int, float)):
                    numeric_keys.add(key)

        for key in numeric_keys:
            values = [rec[key] for rec in records if isinstance(rec.get(key), (int, float))]
            if len(values) > 5:
                median_val = sorted(values)[len(values) // 2]
                patterns[key] = {
                    "low_count": sum(1 for x in values if x < median_val),
                    "high_count": sum(1 for x in values if x >= median_val),
                    "trend": (
                        "increasing" if values[-1] > values[0]
                        else "decreasing" if values[-1] < values[0]
                        else "stable"
                    ),
                }
        return patterns

    def detect_anomalies(self, records):
        anomalies = {}
        numeric_keys = set()
        for record in records:
            for key, value in record.items():
                if isinstance(value, (int, float)):
                    numeric_keys.add(key)

        for key in numeric_keys:
            values = [rec[key] for rec in records if isinstance(rec.get(key), (int, float))]
            if len(values) > 5:
                mean_val = sum(values) / len(values)
                std_dev = (sum((x - mean_val) ** 2 for x in values) / len(values)) ** 0.5
                anomalies[key] = [
                    rec for rec in records
                    if rec.get(key) is not None and abs(rec[key] - mean_val) > 2 * std_dev
                ]
        return anomalies

    def run_analysis(self):
        return self.analyze_by_category()


@router.post("/analyse/")
async def analyse(request: Request):
    try:
        json_data = await request.json()

        if not json_data.get("cleaned_data", []):
            return {"status": "success", "analysis_results": {}}

        analyzer = DataAnalyser(json_data)
        results = analyzer.run_analysis()
        return {"status": "success", "analysis_results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analysis error: {str(e)}")
