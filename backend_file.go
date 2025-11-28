package main

import (
	"encoding/json"
	"fmt"
	"html/template"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

type OCRResult struct {
	Success  bool   `json:"success"`
	TextFile string `json:"text_file"`
	PDFFile  string `json:"pdf_file"`
	Error    string `json:"error"`
}

type PageData struct {
	Message    string
	Error      string
	TextFile   string
	PDFFile    string
	ShowResult bool
}

func main() {
	// Serve static files (for downloads)
	http.HandleFunc("/", homeHandler)
	http.HandleFunc("/upload", uploadHandler)
	http.Handle("/download/", http.StripPrefix("/download/", http.FileServer(http.Dir("."))))

	port := ":8080"
	fmt.Printf("Server starting on http://localhost%s\n", port)
	log.Fatal(http.ListenAndServe(port, nil))
}

func homeHandler(w http.ResponseWriter, r *http.Request) {
	tmpl := template.Must(template.ParseFiles("templates/index.html"))
	data := PageData{
		Message: "Upload your PDF file for OCR processing",
	}
	tmpl.Execute(w, data)
}

func uploadHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Redirect(w, r, "/", http.StatusSeeOther)
		return
	}

	// Parse multipart form (32 MB max)
	err := r.ParseMultipartForm(32 << 20)
	if err != nil {
		renderError(w, "Error parsing form: "+err.Error())
		return
	}

	// Get the file from form
	file, handler, err := r.FormFile("pdffile")
	if err != nil {
		renderError(w, "Error retrieving file: "+err.Error())
		return
	}
	defer file.Close()

	// Validate file extension
	if !strings.HasSuffix(strings.ToLower(handler.Filename), ".pdf") {
		renderError(w, "Please upload a PDF file")
		return
	}

	// Extract filename without extension
	filename := handler.Filename
	baseFilename := strings.TrimSuffix(filename, filepath.Ext(filename))

	// Create directories
	userFileDir := filepath.Join("user_file", baseFilename)
	userFileSearchableDir := filepath.Join("user_file_searchable", baseFilename)

	err = os.MkdirAll(userFileDir, 0755)
	if err != nil {
		renderError(w, "Error creating user_file directory: "+err.Error())
		return
	}

	err = os.MkdirAll(userFileSearchableDir, 0755)
	if err != nil {
		renderError(w, "Error creating user_file_searchable directory: "+err.Error())
		return
	}

	// Save uploaded file
	uploadedFilePath := filepath.Join(userFileDir, filename)
	dst, err := os.Create(uploadedFilePath)
	if err != nil {
		renderError(w, "Error saving file: "+err.Error())
		return
	}
	defer dst.Close()

	_, err = io.Copy(dst, file)
	if err != nil {
		renderError(w, "Error writing file: "+err.Error())
		return
	}

	// Convert paths to absolute paths
	absUploadedPath, _ := filepath.Abs(uploadedFilePath)
	absSearchableDir, _ := filepath.Abs(userFileSearchableDir)

	// Call Python OCR script
	cmd := exec.Command("python", "ocr_python.py", absUploadedPath, absSearchableDir, baseFilename+"_searchable")
	output, err := cmd.CombinedOutput()
	if err != nil {
		renderError(w, fmt.Sprintf("Error running OCR: %s\nOutput: %s", err.Error(), string(output)))
		return
	}

	// Extract JSON from output (in case there are warnings before the JSON)
	jsonStr := string(output)
	jsonStart := strings.Index(jsonStr, "{")
	if jsonStart == -1 {
		renderError(w, "No valid JSON found in OCR output:\n"+string(output))
		return
	}
	jsonStr = jsonStr[jsonStart:]

	// Parse Python output
	var result OCRResult
	err = json.Unmarshal([]byte(jsonStr), &result)
	if err != nil {
		renderError(w, "Error parsing OCR result: "+err.Error()+"\nOutput: "+string(output))
		return
	}

	if !result.Success {
		renderError(w, "OCR processing failed: "+result.Error)
		return
	}

	// Get current working directory
	cwd, err := os.Getwd()
	if err != nil {
		cwd = ""
	}

	// Create relative download paths
	textFileRel, err := filepath.Rel(cwd, result.TextFile)
	if err != nil {
		textFileRel = result.TextFile
	}
	pdfFileRel, err := filepath.Rel(cwd, result.PDFFile)
	if err != nil {
		pdfFileRel = result.PDFFile
	}

	// Convert to forward slashes for URL
	textFileRel = filepath.ToSlash(textFileRel)
	pdfFileRel = filepath.ToSlash(pdfFileRel)

	// Render success page with download links
	tmpl := template.Must(template.ParseFiles("templates/index.html"))
	data := PageData{
		Message:    "OCR processing completed successfully!",
		ShowResult: true,
		TextFile:   "/download/" + textFileRel,
		PDFFile:    "/download/" + pdfFileRel,
	}
	tmpl.Execute(w, data)
}

func renderError(w http.ResponseWriter, errorMsg string) {
	tmpl := template.Must(template.ParseFiles("templates/index.html"))
	data := PageData{
		Error: errorMsg,
	}
	tmpl.Execute(w, data)
}
