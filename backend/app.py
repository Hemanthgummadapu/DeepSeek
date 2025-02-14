from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import pytesseract
from pdf2image import convert_from_path
import tempfile
import subprocess
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from datetime import datetime

# Initialize FastAPI app
app = FastAPI()

# Logging utility
def log(message):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

# Load DeepSeek model
log("🚀 Loading DeepSeek model...")
MODEL_NAME = "deepseek-ai/deepseek-coder-6.7b-instruct"
device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    device_map="auto" if device == "cuda" else None
)

log(f"✅ DeepSeek model loaded successfully on {device.upper()}")

# PDF text extraction function
def extract_text_from_pdf(pdf_path):
    try:
        log(f"🔍 Running pdftotext on {pdf_path}")
        result = subprocess.run(["pdftotext", pdf_path, "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            log("✅ Extracted text using pdftotext.")
            return result.stdout.strip()

        # If pdftotext fails, use OCR
        log(f"⚠️ pdftotext failed: {result.stderr.strip()}")
        log("⚠️ Falling back to OCR (Tesseract)...")

        images = convert_from_path(pdf_path)
        extracted_text_list = [pytesseract.image_to_string(img) for img in images]
        return " ".join(extracted_text_list).strip() if extracted_text_list else "❌ No valid text extracted."

    except Exception as e:
        log(f"❌ Error extracting text: {e}")
        return "❌ Error extracting text."

# Define request structure for question generation
class GenerateRequest(BaseModel):
    context: str
    num_questions: int = 5

# AI question generation function
def generate_questions_finetuned(context, num_questions=5):
    prompt = f"""
    Generate exactly {num_questions} multiple-choice questions based on the given context.
    Each question should have four answer choices.

    - The correct answer must be explicitly labeled using **CorrectAnswer:** before stating the correct option.
    - Provide a **Hint** that guides the user without directly indicating the correct choice.
    - Include an **Explanation** that justifies why the correct answer is correct.

    Context:
    {context}

    Output Format:
    1. Question?
       a) Option 1
       b) Option 2
       c) Option 3
       d) Option 4
       **CorrectAnswer:** "X"
       **Hint:** Consider relevant concepts or historical facts related to the question.
       **Explanation:** "X" is correct because [detailed reason].

    Questions:
    """
    try:
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        output = model.generate(**inputs, max_new_tokens=1024, temperature=0.7)
        return tokenizer.decode(output[0], skip_special_tokens=True)
    except Exception as e:
        log(f"❌ Error generating questions: {e}")
        return "❌ Error generating questions."

# API Endpoints

@app.get("/")
def home():
    """Root route to confirm server is running."""
    return {"message": "DeepSeek Backend is Running!"}

@app.post("/process-pdf/")
async def process_pdf(file: UploadFile = File(...)):
    """Extracts text from uploaded PDF file."""
    log(f"✅ Received file: {file.filename}")

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        tmp_file.write(file.file.read())
        tmp_file_path = tmp_file.name
        tmp_file.close()

        log(f"✅ Saved uploaded file as: {tmp_file_path}")

        extracted_text = extract_text_from_pdf(tmp_file_path)
        os.remove(tmp_file_path)  # Cleanup

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No text extracted from the PDF.")

        return {"status": "text_extracted", "message": "Text extracted successfully!", "context": extracted_text}

    except Exception as e:
        log(f"❌ Error processing PDF: {e}")
        os.remove(tmp_file.name)  # Cleanup
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/generate-questions/")
def generate_questions_endpoint(request: GenerateRequest):
    """Generates AI-based multiple-choice questions."""
    if not request.context.strip():
        raise HTTPException(status_code=400, detail="Context is required to generate questions.")

    try:
        questions = generate_questions_finetuned(request.context[:1500], num_questions=request.num_questions)
        return {"status": "questions_generated", "message": "Questions generated successfully!", "questions": questions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while generating questions: {str(e)}")

# Start the server
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
