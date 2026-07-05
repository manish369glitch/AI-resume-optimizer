import os
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import pdfplumber
from dotenv import load_dotenv   

load_dotenv()

app = FastAPI(title="Resume Optimizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Gemini Client directly with your key
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Outgoing data validation structures for FastAPI
class BulletPointRewrite(BaseModel):
    original: str = Field(description="The original bullet point from the resume.")
    suggested: str = Field(description="The optimized rewrite containing strong verbs or missing metrics.")

class OptimizationResponse(BaseModel):
    match_percentage: int = Field(description="A score from 0 to 100 indicating how well the resume matches the JD.")
    missing_hard_skills: list[str] = Field(description="Critical technical skills, tools, or languages mentioned in the JD but missing from the resume.")
    missing_soft_skills: list[str] = Field(description="Soft skills or methodologies missing from the resume.")
    ats_warnings: list[str] = Field(description="Formatting or structural issues that might trip up an ATS.")
    bullet_point_improvements: list[BulletPointRewrite] = Field(
        description="List of specific bullet points from the resume rewritten to include missing keywords or use stronger action verbs."
    )

def extract_text_from_pdf(file: UploadFile) -> str:
    text = ""
    try:
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="The uploaded PDF appears to be empty or unscannable images.")
    return text

@app.post("/api/optimize", response_model=OptimizationResponse)
async def optimize_resume(
    resume_file: UploadFile = File(..., description="The resume PDF file"),
    job_description: str = Form(..., description="[Company Name] is a technology-driven organization building the next generation of intelligent software solutions. We are seeking a talented Computer Scientist to join our research and development team to push the boundaries of computational theory and applied machine learning.")
):
    resume_text = extract_text_from_pdf(resume_file)
    
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) optimization algorithm and executive recruiter.
    Analyze the provided Resume against the Job Description. 
    
    Perform a deep gap analysis and return the results strictly matching the requested JSON structure.
    Provide realistic, impact-driven bullet point improvements using strong action verbs.

    You must output your complete response in valid JSON matching this layout exactly:
    {{
        "match_percentage": 75,
        "missing_hard_skills": ["Skill A", "Skill B"],
        "missing_soft_skills": ["Skill C"],
        "ats_warnings": ["Warning Text"],
        "bullet_point_improvements": [
            {{
                "original": "Old bullet text",
                "suggested": "New bullet text"
            }}
        ]
    }}

    JOB DESCRIPTION:
    \"\"\"{job_description}\"\"\"

    RESUME:
    \"\"\"{resume_text}\"\"\"
    """

    try:
        # We removed response_schema entirely so the SDK stops injecting forbidden keys
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)