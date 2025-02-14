import React, { useState } from "react";
import axios from "axios";

// Load backend URL from environment variable
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [file, setFile] = useState(null);
  const [context, setContext] = useState(""); // Holds extracted text
  const [questions, setQuestions] = useState(""); // Holds generated questions (plain text)
  const [status, setStatus] = useState(""); // Status messages
  const [loading, setLoading] = useState(false); // Loading state

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      alert("Please upload a PDF file!");
      return;
    }

    setStatus("Processing your PDF...");
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Step 1: Extract text from PDF
      const response = await axios.post(`${BACKEND_URL}/process-pdf`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      console.log("Extracted Context:", response.data.context);

      if (response.data.status === "text_extracted") {
        setStatus("✅ Text extracted from PDF successfully!");
        setContext(response.data.context);

        // Step 2: Generate questions using DeepSeek
        const questionResponse = await axios.post(`${BACKEND_URL}/generate-questions`, {
          context: response.data.context,
        });

        console.log("Generated Questions:", questionResponse.data.questions);

        if (questionResponse.data.status === "questions_generated") {
          setStatus("✅ Questions generated successfully!");
          setQuestions(questionResponse.data.questions);
        } else {
          setStatus("❌ Failed to generate questions.");
        }
      }
    } catch (error) {
      console.error("Error processing PDF:", error);
      setStatus("❌ Failed to process PDF!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>📄 Trivia Generator (DeepSeek Model)</h1>

      <form onSubmit={handleSubmit}>
        <input type="file" accept="application/pdf" onChange={handleFileChange} />
        <button type="submit" disabled={loading || !file} style={{ marginLeft: "10px" }}>
          {loading ? "⏳ Processing..." : "🚀 Submit"}
        </button>
      </form>

      {status && (
        <div
          style={{
            marginTop: "10px",
            fontWeight: "bold",
            color: status.includes("❌") ? "red" : status.includes("✅") ? "green" : "black",
          }}
        >
          {status}
        </div>
      )}

      {context && (
        <div style={{ marginTop: "20px" }}>
          <h2>📜 Extracted Context:</h2>
          <textarea
            value={context}
            readOnly
            rows="6"
            style={{ width: "100%", background: "#333", color: "#fff", padding: "10px" }}
          />
        </div>
      )}

      {questions && (
        <div style={{ marginTop: "20px" }}>
          <h2>❓ Generated Questions:</h2>
          <pre
            style={{
              background: "#222",
              color: "#fff",
              padding: "10px",
              borderRadius: "5px",
              whiteSpace: "pre-wrap",
            }}
          >
            {questions}
          </pre>
        </div>
      )}
    </div>
  );
}

export default App;
