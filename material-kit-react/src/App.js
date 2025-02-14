import React, { useState } from "react";
import axios from "axios";
import {
  Button,
  Typography,
  Container,
  Box,
  Paper,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  AppBar,
  Toolbar,
  Snackbar,
} from "@mui/material";
import { CloudUpload as CloudUploadIcon } from "@mui/icons-material";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { motion } from "framer-motion";
import Logo from "./assets/images/LV (2).png"; // Correct logo path

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#00bcd4" },
    secondary: { main: "#ff4081" },
    background: { default: "#121212", paper: "rgba(255, 255, 255, 0.08)" },
  },
  typography: { fontFamily: "Poppins, Arial, sans-serif", h6: { fontWeight: 700 } },
});

function App() {
  const [file, setFile] = useState(null);
  const [context, setContext] = useState("");
  const [questions, setQuestions] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [openSnackbar, setOpenSnackbar] = useState(false);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) {
      alert("Please upload a file!");
      return;
    }

    setLoading(true);
    setStatusMessage("Processing PDF...");
    setOpenSnackbar(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Step 1: Extract text from PDF
      const API_URL = process.env.REACT_APP_BACKEND_URL;

      const response = await axios.post(`${API_URL}/process-pdf`, formData, {
              headers: { "Content-Type": "multipart/form-data" },
      });

      if (response.data.status === "text_extracted") {
        setStatusMessage("✅ Text extracted successfully!");
        setContext(response.data.context);

        // Step 2: Generate questions using DeepSeek
        const API_URL = process.env.REACT_APP_BACKEND_URL;

        const response = await axios.post(`${API_URL}/process-pdf`, formData, {
                  context: response.data.context,
        });

        if (questionResponse.data.status === "questions_generated") {
          setStatusMessage("✅ Questions generated successfully!");
          setQuestions(questionResponse.data.questions);
        } else {
          setStatusMessage("❌ Failed to generate questions.");
        }
      }
    } catch (error) {
      console.error("Error processing PDF:", error);
      setStatusMessage("❌ Failed to process PDF!");
    } finally {
      setLoading(false);
      setOpenSnackbar(true);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <Container maxWidth="md" sx={{ padding: "20px", borderRadius: 2 }}>
        {/* Navbar */}
        <AppBar position="static" sx={{ marginBottom: "20px", backgroundColor: "#181818", padding: "20px 0" }}>
          <Toolbar sx={{ flexDirection: "column", alignItems: "center" }}>
            <img
              src={Logo}
              alt="Logo"
              style={{ width: "60px", marginBottom: "10px", animation: "pulse 2s infinite ease-in-out" }}
            />
            <Typography
              variant="h4"
              component={motion.div}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              sx={{
                fontWeight: "bold",
                fontSize: "2.5rem",
                background: "linear-gradient(90deg, #1E90FF, #00BFFF, #87CEFA)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                textAlign: "center",
                textShadow: "0px 0px 10px rgba(30, 144, 255, 0.6), 0px 0px 10px rgba(0, 191, 255, 0.6)",
                border: "2px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "10px",
                padding: "10px 20px",
              }}
            >
              Lidvizion's Trivia Generator
            </Typography>
          </Toolbar>
        </AppBar>

        {/* File Upload Section */}
        <Paper elevation={4} sx={{ padding: "30px", marginBottom: "30px", borderRadius: 3 }}>
          <Typography variant="h6" gutterBottom>Upload a PDF to Generate Trivia Questions</Typography>
          <form onSubmit={handleSubmit}>
            <Box sx={{ display: "flex", alignItems: "center", border: "1px solid #ccc", padding: "10px", borderRadius: "5px" }}>
              <CloudUploadIcon sx={{ marginRight: "10px" }} />
              <input type="file" accept="application/pdf" onChange={handleFileChange} style={{ flexGrow: 1 }} />
            </Box>
            <Box mt={2}>
              <Button type="submit" variant="contained" color="primary" fullWidth sx={{ padding: "12px" }}>
                {loading ? "Processing..." : "Submit"}
              </Button>
            </Box>
          </form>
        </Paper>

        {/* Show Status Messages */}
        {statusMessage && <Typography variant="h6" sx={{ textAlign: "center", marginTop: "10px", color: "#00bcd4" }}>{statusMessage}</Typography>}

        {/* Show Loading Spinner */}
        {loading && <Box sx={{ textAlign: "center", marginTop: "20px" }}><CircularProgress sx={{ color: "#ffffff" }} /></Box>}

        {/* Extracted Context */}
        {context && (
          <Box mt={4}>
            <Typography variant="h6" gutterBottom>Extracted Context:</Typography>
            <Paper elevation={2} sx={{ padding: "20px", height: "300px", overflowY: "scroll", backgroundColor: "#333", borderRadius: "10px" }}>
              <Typography variant="body1">{context}</Typography>
            </Paper>
          </Box>
        )}

        {/* Generated Questions */}
        {questions && (
          <Box mt={4}>
            <Typography variant="h6" gutterBottom>Generated Questions:</Typography>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card sx={{ padding: "15px", borderRadius: 3 }}>
                  <CardContent>
                    <Typography variant="body1" sx={{ color: "#00bcd4", whiteSpace: "pre-wrap" }}>
                      {questions}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Snackbar for Status Updates */}
        <Snackbar
          open={openSnackbar}
          autoHideDuration={3000}
          onClose={() => setOpenSnackbar(false)}
          message={statusMessage}
          anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
        />
      </Container>
    </ThemeProvider>
  );
}

export default App;
