import json
import requests
from tkinter import Tk, filedialog

# Your deployed API endpoint
API_URL = "https://h0gn7fm71g.execute-api.ap-southeast-2.amazonaws.com/dev/preprocess"

def choose_file():
    """Open a file dialog and return the selected file path."""
    Tk().withdraw()  # Hide root window
    file_path = filedialog.askopenfilename(
        title="Select JSON File",
        filetypes=[("JSON Files", "*.json")]
    )
    return file_path

def upload_and_preprocess(file_path):
    with open(file_path, "rb") as f:
        files = {"file": (file_path.split("/")[-1], f, "application/json")}
        response = requests.post(API_URL, files=files)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("Choose a JSON file to upload for preprocessing.")
    selected_file = choose_file()
    if selected_file:
        upload_and_preprocess(selected_file)
    else:
        print("No file selected.")
