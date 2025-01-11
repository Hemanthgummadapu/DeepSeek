import streamlit as st
from transformers import T5Tokenizer, T5ForConditionalGeneration
from sentence_transformers import SentenceTransformer, util
import torch
import openai
import pytesseract
from pdf2image import convert_from_path
import tempfile
import os

# Set OpenAI API key
openai.api_key = "REMOVED"

# Load models
model_name = "doc2query/msmarco-t5-base-v1"
tokenizer = T5Tokenizer.from_pretrained(model_name)
t5_model = T5ForConditionalGeneration.from_pretrained(model_name)
similarity_model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda" if torch.cuda.is_available() else "cpu")

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF using OCR."""
    try:
        text = ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(pdf_file.read())
            images = convert_from_path(tmp_file.name)
            for img in images:
                text += pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return None
def generate_questions(context, num_questions=5, similarity_threshold=0.8):
    """Generate unique questions from the given context."""
    try:
        input_text = f"Generate questions based on the following context: {context}"
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True).to(t5_model.device)
        outputs = t5_model.generate(
            **inputs,
            max_length=50,
            num_return_sequences=num_questions,
            num_beams=5,
            early_stopping=True
        )
        questions = [tokenizer.decode(o, skip_special_tokens=True) for o in outputs]
        embeddings = similarity_model.encode(questions, convert_to_tensor=True)
        
        final_questions = []
        for idx, question in enumerate(questions):
            if not any(util.cos_sim(embeddings[idx], embeddings[j]).item() >= similarity_threshold for j in range(len(final_questions))):
                final_questions.append(question)
                if len(final_questions) >= num_questions:
                    break
        return final_questions
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return []
import json

def build_question_schema(question, context):
    """Generate a schema for a question using GPT-4."""
    prompt = (
        f"Context: {context}\n"
        f"Question: {question}\n"
        "Generate the following JSON format:\n"
        "{\n"
        "  \"correct_answer\": \"[Correct Answer]\",\n"
        "  \"wrong_answers\": [\"Wrong Option 1\", \"Wrong Option 2\", \"Wrong Option 3\"],\n"
        "  \"hints\": [\"Hint 1\", \"Hint 2\"],\n"
        "  \"explanation\": \"[Provide a clear and concise explanation of the answer.]\"\n"
        "}"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an educational assistant that provides JSON-formatted answers."},
                {"role": "user", "content": prompt}
            ]
        )
        # Get the response content
        content = response["choices"][0]["message"]["content"]
        
        # Parse JSON
        try:
            schema = json.loads(content)
            return schema
        except json.JSONDecodeError:
           # Handle invalid JSON gracefully
            st.error(f"JSON Parse Error: Could not parse the following response:\n{content}")
            return {"error": f"Invalid JSON: {content}"}
    except Exception as e:
        st.error(f"Error generating schema: {e}")
        return {"error": f"GPT-4 Error: {str(e)}"}
        
# Streamlit UI
st.title("Lidvizion's Trivia Generator - PDF Question Generator")
st.write(
    "Welcome to Lidvizion's Trivia Generator! Upload a PDF file to extract text, "
    "generate trivia questions"
)
# File upload
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    st.info("Processing your PDF...")
    
    # Extract context
    context = extract_text_from_pdf(uploaded_file)
    if context:
        st.success("Text extracted from PDF successfully!")
        st.text_area("Extracted Context", context, height=200)
        
        # Generate questions
        with st.spinner("Generating questions..."):
            questions = generate_questions(context, num_questions=5)
        if questions:
            st.success("Questions generated successfully!")           st.write("### Generated Questions:")
            for i, question in enumerate(questions, 1):
                st.write(f"{i}. {question}")
                
            # Build schemas
            st.write("### Question Schemas:")
            schemas = []
            for question in questions:
                with st.spinner(f"Generating schema for: {question}"):
                    schema = build_question_schema(question, context) 
                    schemas.append({"question": question, "schema": schema})
                    st.write(f"**Question:** {question}")
                    st.json(schema)
        else:
            st.error("Failed to generate questions from the context.")
    else:
        st.error("Failed to extract text from the PDF.")
        
