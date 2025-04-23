import json
import requests

# AWS API Gateway Endpoints
PREPROCESS_URL = "https://h0gn7fm71g.execute-api.ap-southeast-2.amazonaws.com/dev/preprocess"
ANALYSE_URL = "https://h0gn7fm71g.execute-api.ap-southeast-2.amazonaws.com/dev/analyse"

def main():
    print("Paste your raw JSON data below:")
    user_input = input()

    try:
        raw_data = json.loads(user_input)  # Validate & parse input

        # Step 1: Preprocess
        preprocess_response = requests.post(
            PREPROCESS_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(raw_data)
        )

        if preprocess_response.status_code == 200:
            preprocessed_data = preprocess_response.json()

            # Step 2: Analyse
            analyse_response = requests.post(
                ANALYSE_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps(preprocessed_data)
            )

            if analyse_response.status_code == 200:
                analysed_data = analyse_response.json()
                print(json.dumps(analysed_data, indent=4))
            else:
                print(f"\nError during analysis: {analyse_response.status_code}")
                print(analyse_response.text)
        else:
            print(f"\nError during preprocessing: {preprocess_response.status_code}")
            print(preprocess_response.text)

    except json.JSONDecodeError:
        print("Invalid JSON input. Please check your data.")

if __name__ == "__main__":
    main()
