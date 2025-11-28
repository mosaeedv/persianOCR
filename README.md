# PDF OCR Service - Go Backend with Python OCR

This project provides a web-based PDF OCR service using Go backend and Python OCR processing.

## 📁 Project Structure

```
F:\goproject\
├── ocr_python.py              # Python OCR script
├── backend_file.go            # Go backend server
├── templates/
│   └── index.html            # Web interface
├── user_file/                # Created automatically - stores uploaded PDFs
└── user_file_searchable/     # Created automatically - stores OCR results
```

## 🔧 Prerequisites

### Required Software:

1. **Go** (version 1.16 or higher)
   - Download from: https://golang.org/dl/
   
2. **Python** (version 3.7 or higher)
   - Download from: https://www.python.org/downloads/

3. **Tesseract OCR**
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install to: `C:\Program Files\Tesseract-OCR\`
   
4. **Poppler**
   - Download from: https://github.com/oschwartz10612/poppler-windows/releases
   - Extract to: `C:\Program Files\poppler-24.08.0\`

### Python Dependencies:

Install the required Python packages:

```bash
pip install pdf2image Pillow pytesseract PyPDF2
```

## 🚀 Setup Instructions

### Step 1: Create Project Directory

Create the project folder at `F:\goproject` and copy all files:

```
F:\goproject\
├── ocr_python.py
├── backend_file.go
└── templates\
    └── index.html
```

### Step 2: Verify Tesseract and Poppler Installation

Make sure the paths in `ocr_python.py` match your installation:

```python
tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"
```

If your installations are in different locations, update these paths.

### Step 3: Initialize Go Module

Open Command Prompt or PowerShell in `F:\goproject` and run:

```bash
go mod init goproject
go mod tidy
```

## ▶️ Running the Application

### Step 1: Start the Server

In the `F:\goproject` directory, run:

```bash
go run backend_file.go
```

You should see:
```
Server starting on http://localhost:8080
```

### Step 2: Access the Web Interface

Open your browser and go to:
```
http://localhost:8080
```

### Step 3: Upload and Process PDF

1. Click "Click to select PDF file"
2. Choose a PDF file (e.g., `hw1.pdf`)
3. Click "Process PDF"
4. Wait for processing to complete
5. Download the results:
   - Text file (`.txt`) - extracted text
   - Searchable PDF - OCR'd PDF with searchable text layer

## 📝 How It Works

1. **User uploads PDF** → Saved to `user_file/hw1/hw1.pdf`
2. **Go creates directories**:
   - `user_file/hw1/`
   - `user_file_searchable/hw1/`
3. **Go calls Python** → Passes file path to Python script
4. **Python processes**:
   - Converts PDF to images
   - Performs OCR (English + Persian)
   - Creates searchable PDF
   - Saves to `user_file_searchable/hw1/`
5. **Python returns paths** → JSON response with file locations
6. **Go provides download links** → User can download results

## 🔍 Directory Structure After Upload

```
F:\goproject\
├── user_file/
│   └── hw1/
│       └── hw1.pdf                          # Original uploaded file
└── user_file_searchable/
    └── hw1/
        ├── hw1_searchable.txt               # Extracted text
        └── hw1_searchable_searchable.pdf    # Searchable PDF
```

## 🛠️ Troubleshooting

### Error: "Tesseract not found"
- Verify Tesseract is installed at: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Update the path in `ocr_python.py` if installed elsewhere

### Error: "Poppler not found"
- Verify Poppler is extracted to: `C:\Program Files\poppler-24.08.0\`
- Update the path in `ocr_python.py` if extracted elsewhere

### Error: "Python module not found"
- Install missing modules: `pip install pdf2image Pillow pytesseract PyPDF2`

### Error: "Port 8080 already in use"
- Change the port in `backend_file.go`:
  ```go
  port := ":8080"  // Change to ":8081" or another port
  ```

## 🎨 Customization

### Change OCR Languages

Edit `ocr_python.py`:
```python
languages = "eng+fas"  # Change to your desired languages
# Examples:
# "eng" - English only
# "eng+ara" - English + Arabic
# "eng+fra" - English + French
```

### Change Upload Size Limit

Edit `backend_file.go`:
```go
err := r.ParseMultipartForm(32 << 20)  // 32 MB
// Change to: 64 << 20 for 64 MB
```

### Customize HTML Interface

Edit `templates/index.html` to change colors, text, or layout.

## 📊 Features

- ✅ Simple web interface
- ✅ PDF file upload
- ✅ Multi-language OCR (English + Persian)
- ✅ Searchable PDF generation
- ✅ Text extraction
- ✅ Automatic directory management
- ✅ Download links for results
- ✅ Error handling and validation
- ✅ Progress indication

## 🔒 Security Notes

- This is a localhost development version
- For production use, add:
  - File size validation
  - File type validation
  - Rate limiting
  - User authentication
  - HTTPS encryption
  - Input sanitization

## 📄 License

This is a sample project for educational purposes.

## 🤝 Contributing

Feel free to modify and improve this project for your needs!
