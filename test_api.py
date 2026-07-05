import os
import requests
import tkinter as tk
from tkinter import filedialog
import pprint

# 1. Open a native Windows file selection dialog
print("Opening file selector... Please choose your resume PDF.")
root = tk.Tk()
root.withdraw() # Hide the main tiny blank tkinter window
file_path = filedialog.askopenfilename(
    title="Select your Resume PDF",
    filetypes=[("PDF Files", "*.pdf")]
)

if not file_path:
    print("❌ No file selected. Exiting script.")
    exit()

print(f"Selected file: {file_path}")

# 2. Fire the request to your API
url = "http://127.0.0.1:8000/api/optimize"
job_desc = """
The Customer Service Representative serves as the primary point of contact for our clients, 
ensuring a welcoming and supportive experience. You will be responsible for resolving customer inquiries, 
processing orders, and identifying customer needs to guarantee satisfaction and retention.
"""

payload = {"job_description": job_desc}

try:
    with open(file_path, "rb") as f:
        files = {"resume_file": (os.path.basename(file_path), f, "application/pdf")}
        print("\nSending request to your Resume Optimizer API... (waiting for Gemini)")
        response = requests.post(url, data=payload, files=files)

    if response.status_code == 200:
        print("\n🎉 SUCCESS! Here is your structured AI analysis:\n")
        pprint.pprint(response.json())
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"\n❌ Connection failed: {str(e)}")