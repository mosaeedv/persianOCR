# 🚀 Quick Start Guide

## Prerequisites Check

Before starting, make sure you have installed:

- [ ] Go (https://golang.org/dl/)
- [ ] Python (https://www.python.org/downloads/)
- [ ] Tesseract OCR (https://github.com/UB-Mannheim/tesseract/wiki)
- [ ] Poppler (https://github.com/oschwartz10612/poppler-windows/releases)

## Installation Steps

### 1. Copy Files to F:\goproject

Copy all files from this folder to `F:\goproject`:

```
F:\goproject\
├── ocr_python.py
├── backend_file.go
├── start_server.bat
├── requirements.txt
├── .gitignore
├── README.md
├── QUICK_START.md
└── templates\
    └── index.html
```

### 2. Install Python Dependencies

Open Command Prompt in `F:\goproject` and run:

```bash
pip install -r requirements.txt
```

Or manually install:

```bash
pip install pdf2image Pillow pytesseract PyPDF2
```

### 3. Verify Paths in ocr_python.py

Open `ocr_python.py` and check these paths match your installation:

```python
tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"
```

Update them if your installations are in different locations.

### 4. Initialize Go Module

In `F:\goproject`, run:

```bash
go mod init goproject
```

## Running the Server

### Method 1: Using Batch File (Easiest)

Double-click `start_server.bat`

### Method 2: Using Command Line

Open Command Prompt in `F:\goproject` and run:

```bash
go run backend_file.go
```

## Using the Application

1. Open browser: http://localhost:8080
2. Click "Click to select PDF file"
3. Choose your PDF (e.g., hw1.pdf)
4. Click "Process PDF"
5. Wait for processing
6. Download your files:
   - Text file (.txt)
   - Searchable PDF

## Expected Output

For a file named `hw1.pdf`, you'll get:

```
F:\goproject\
├── user_file\
│   └── hw1\
│       └── hw1.pdf
└── user_file_searchable\
    └── hw1\
        ├── hw1_searchable.txt
        └── hw1_searchable_searchable.pdf
```

## Troubleshooting

### Server won't start?
- Check if Go is installed: `go version`
- Check if Python is installed: `python --version`
- Check if port 8080 is free

### "Tesseract not found" error?
- Verify Tesseract installation path
- Update path in `ocr_python.py`

### "Module not found" error?
- Run: `pip install -r requirements.txt`
- Or install modules individually

### Can't upload files?
- Check file is a valid PDF
- Check file size (default limit: 32 MB)

## Testing

Test with a simple PDF:
1. Create a PDF with some text
2. Upload through the web interface
3. Check if you get both .txt and searchable PDF back

## Next Steps

Once everything works:
- Process your actual PDFs
- Customize the HTML interface
- Change OCR languages if needed
- Adjust upload size limits

## Need Help?

Check the full README.md for detailed documentation.

---

Enjoy your PDF OCR service! 🎉
