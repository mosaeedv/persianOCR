"""
OCR Python Script - HOCR version with RTL markers

Uses HOCR output to extract text word by word and adds RTL markers
for Persian/Arabic words. Includes logging of all changes.

Install:
    pip install pdf2image pillow pytesseract PyPDF2 pikepdf lxml
"""

import os
import sys
import json
import re
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from PyPDF2 import PdfMerger
from io import BytesIO
from datetime import datetime
from lxml import etree

try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False
    print("Warning: pikepdf not available, using fallback method", file=sys.stderr)


# =============================================================================
# RTL DETECTION
# =============================================================================

def is_rtl_char(char):
    """Check if a character is RTL (Arabic/Persian/Hebrew)"""
    code = ord(char)
    return (
        0x0600 <= code <= 0x06FF or   # Arabic
        0x0750 <= code <= 0x077F or   # Arabic Supplement
        0xFB50 <= code <= 0xFDFF or   # Arabic Presentation Forms-A
        0xFE70 <= code <= 0xFEFF or   # Arabic Presentation Forms-B
        0x0590 <= code <= 0x05FF or   # Hebrew
        0xFB00 <= code <= 0xFB4F      # Hebrew Presentation Forms
    )


def is_rtl_word(word):
    """Check if a word contains RTL characters (Persian/Arabic/Hebrew)"""
    if not word:
        return False
    rtl_count = sum(1 for char in word if is_rtl_char(char))
    # Consider it RTL if more than 50% of non-space chars are RTL
    non_space = len([c for c in word if not c.isspace()])
    return rtl_count > non_space / 2 if non_space > 0 else False


def is_rtl_line(words):
    """Check if a line is predominantly RTL"""
    if not words:
        return False
    rtl_count = sum(1 for w in words if is_rtl_word(w))
    return rtl_count > len(words) / 2


# =============================================================================
# HOCR PARSING
# =============================================================================

def parse_hocr(hocr_bytes):
    """
    Parse HOCR XML and extract words with their text.
    Returns list of words in reading order.
    """
    try:
        # Parse HOCR XML
        root = etree.fromstring(hocr_bytes)
        
        # Find all word spans (ocrx_word class)
        namespaces = {'html': 'http://www.w3.org/1999/xhtml'}
        
        # Try with namespace first, then without
        words = root.xpath("//html:span[@class='ocrx_word']", namespaces=namespaces)
        if not words:
            words = root.xpath("//*[@class='ocrx_word']")
        
        # Also try ocr_word class (some Tesseract versions)
        if not words:
            words = root.xpath("//html:span[@class='ocr_word']", namespaces=namespaces)
        if not words:
            words = root.xpath("//*[@class='ocr_word']")
        
        extracted_words = []
        for word_elem in words:
            text = ''.join(word_elem.itertext()).strip()
            if text:
                extracted_words.append(text)
        
        return extracted_words
        
    except Exception as e:
        print(f"HOCR parsing error: {e}", file=sys.stderr)
        return []


def extract_lines_from_hocr(hocr_bytes):
    """
    Parse HOCR and extract text line by line, preserving structure.
    Returns list of lines, each line is a list of words.
    """
    try:
        root = etree.fromstring(hocr_bytes)
        namespaces = {'html': 'http://www.w3.org/1999/xhtml'}
        
        # Find all lines
        lines = root.xpath("//html:span[@class='ocr_line']", namespaces=namespaces)
        if not lines:
            lines = root.xpath("//*[@class='ocr_line']")
        
        extracted_lines = []
        for line_elem in lines:
            # Get words in this line
            words = line_elem.xpath(".//html:span[@class='ocrx_word']", namespaces=namespaces)
            if not words:
                words = line_elem.xpath(".//*[@class='ocrx_word']")
            if not words:
                words = line_elem.xpath(".//html:span[@class='ocr_word']", namespaces=namespaces)
            if not words:
                words = line_elem.xpath(".//*[@class='ocr_word']")
            
            line_words = []
            for word_elem in words:
                text = ''.join(word_elem.itertext()).strip()
                if text:
                    line_words.append(text)
            
            if line_words:
                extracted_lines.append(line_words)
        
        return extracted_lines
        
    except Exception as e:
        print(f"HOCR line parsing error: {e}", file=sys.stderr)
        return []


# =============================================================================
# TEXT EXTRACTION WITH RTL MARKERS
# =============================================================================

class RTLLogger:
    """Tracks RTL line reversals for logging"""
    
    def __init__(self):
        self.total_words = 0
        self.rtl_words = 0
        self.lines_reversed = 0
        self.page_stats = []
        self.log_entries = []
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.log_entries.append(entry)
    
    def add_page_stats(self, page_num, total, rtl, reversed_lines):
        self.page_stats.append({
            'page': page_num,
            'total_words': total,
            'rtl_words': rtl,
            'lines_reversed': reversed_lines
        })
        self.total_words += total
        self.rtl_words += rtl
        self.lines_reversed += reversed_lines
        self.log(f"Page {page_num}: {total} words ({rtl} RTL), {reversed_lines} lines reversed")
    
    def get_summary(self):
        return {
            'total_words': self.total_words,
            'rtl_words': self.rtl_words,
            'lines_reversed': self.lines_reversed,
            'rtl_percentage': round(100 * self.rtl_words / self.total_words, 1) if self.total_words > 0 else 0,
            'pages': self.page_stats
        }
    
    def write_log(self, filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("OCR RTL LOG\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total words processed: {self.total_words}\n")
            f.write(f"RTL words detected: {self.rtl_words}\n")
            f.write(f"RTL lines reversed: {self.lines_reversed}\n")
            if self.total_words > 0:
                f.write(f"RTL percentage: {100 * self.rtl_words / self.total_words:.1f}%\n")
            f.write("\n")
            
            f.write("PAGE DETAILS\n")
            f.write("-" * 40 + "\n")
            for stat in self.page_stats:
                f.write(f"Page {stat['page']:3d}: {stat['total_words']:5d} words, "
                       f"{stat['rtl_words']:5d} RTL, {stat['lines_reversed']:3d} lines reversed\n")
            f.write("\n")
            
            f.write("PROCESSING LOG\n")
            f.write("-" * 40 + "\n")
            for entry in self.log_entries:
                f.write(entry + "\n")


def extract_text_with_hocr(png_path, languages, page_num, logger):
    """
    Extract text from image using HOCR.
    Reverses word order in RTL lines for correct reading order.
    Keeps text as LTR so selection works left-to-right.
    Returns processed text and updates logger.
    """
    img = Image.open(png_path)
    
    # Get HOCR output
    hocr = pytesseract.image_to_pdf_or_hocr(img, lang=languages, extension='hocr')
    
    # Parse HOCR to get lines and words
    lines = extract_lines_from_hocr(hocr)
    
    # Process lines
    page_total = 0
    page_rtl = 0
    page_reversed = 0
    processed_lines = []
    
    for line_words in lines:
        # Count words
        for word in line_words:
            page_total += 1
            if is_rtl_word(word):
                page_rtl += 1
        
        # Check if line is predominantly RTL
        line_is_rtl = is_rtl_line(line_words)
        
        # If RTL line, reverse word order (keep as LTR, just reorder)
        if line_is_rtl:
            line_words = line_words[::-1]
            page_reversed += 1
        
        # Join words - no markers, just reversed order
        line_text = ' '.join(line_words)
        processed_lines.append(line_text)
    
    # Update logger
    logger.add_page_stats(page_num, page_total, page_rtl, page_reversed)
    
    # Join lines
    page_text = '\n'.join(processed_lines)
    
    return page_text


# =============================================================================
# RTL FIXING FOR PDF - Reverse word order (keep LTR, reverse words)
# =============================================================================

def is_rtl_codepoint(code):
    """Check if Unicode codepoint is RTL"""
    return (0x0600 <= code <= 0x06FF or
            0x0750 <= code <= 0x077F or
            0xFB50 <= code <= 0xFDFF or
            0xFE70 <= code <= 0xFEFF or
            0x0590 <= code <= 0x05FF)


def is_rtl_hex_string(hex_content):
    """Check if hex string contains RTL characters"""
    if not hex_content or len(hex_content) < 4:
        return False
    
    rtl_count = 0
    total = 0
    
    for i in range(0, len(hex_content) - 3, 4):
        try:
            code = int(hex_content[i:i+4], 16)
            if code > 0x007F:  # Non-ASCII
                total += 1
                if is_rtl_codepoint(code):
                    rtl_count += 1
        except:
            pass
    
    return rtl_count > total / 2 if total > 0 else False


def reverse_tj_array(tj_content):
    """
    Reverse the order of elements in a TJ array.
    TJ array example: [<hex1> -10 <hex2> -5 <hex3>]
    Reversed: [<hex3> -5 <hex2> -10 <hex1>]
    """
    # Find all elements: hex strings <...> and numbers
    elements = re.findall(r'<[0-9A-Fa-f]+>|[-]?\d+\.?\d*', tj_content)
    
    if not elements:
        return tj_content
    
    # Check if this array has RTL content
    has_rtl = any(is_rtl_hex_string(e[1:-1]) for e in elements if e.startswith('<'))
    
    if not has_rtl:
        return tj_content
    
    # Reverse the elements
    reversed_elements = elements[::-1]
    
    return '[' + ' '.join(reversed_elements) + ']'


def fix_content_stream_text(content_bytes):
    """Fix RTL text in PDF content stream by reversing word order in TJ arrays"""
    try:
        content = content_bytes.decode('latin-1')
    except:
        return content_bytes
    
    # Pattern for TJ arrays: [...] TJ
    def fix_tj_array(match):
        tj_content = match.group(1)
        fixed = reverse_tj_array(tj_content)
        return fixed + ' TJ'
    
    fixed = re.sub(r'\[(.*?)\]\s*TJ', fix_tj_array, content, flags=re.DOTALL)
    return fixed.encode('latin-1')


def fix_pdf_with_pikepdf(pdf_bytes):
    """Fix RTL text using pikepdf for proper PDF handling."""
    if not PIKEPDF_AVAILABLE:
        return pdf_bytes
    
    try:
        pdf = pikepdf.open(BytesIO(pdf_bytes))
        
        for page in pdf.pages:
            if '/Contents' not in page:
                continue
            
            contents = page.Contents
            
            if isinstance(contents, pikepdf.Array):
                streams = list(contents)
            else:
                streams = [contents]
            
            for stream in streams:
                try:
                    raw_data = stream.read_bytes()
                    
                    if b'TJ' in raw_data or b'Tj' in raw_data:
                        fixed_data = fix_content_stream_text(raw_data)
                        stream.write(fixed_data)
                except Exception as e:
                    print(f"Warning: Could not process stream: {e}", file=sys.stderr)
                    continue
        
        output = BytesIO()
        pdf.save(output)
        pdf.close()
        
        return output.getvalue()
        
    except Exception as e:
        print(f"pikepdf processing failed: {e}", file=sys.stderr)
        return pdf_bytes


def fix_pdf_with_regex(pdf_bytes):
    """Fallback: Fix RTL using regex on raw PDF bytes."""
    import zlib
    
    result = pdf_bytes
    stream_pattern = rb'(stream\r?\n)(.*?)(\r?\nendstream)'
    
    def process_stream(match):
        prefix = match.group(1)
        stream_data = match.group(2)
        suffix = match.group(3)
        
        try:
            decompressed = zlib.decompress(stream_data)
            
            if b'TJ' in decompressed or b'Tj' in decompressed:
                fixed = fix_content_stream_text(decompressed)
                recompressed = zlib.compress(fixed)
                return prefix + recompressed + suffix
        except:
            if b'TJ' in stream_data or b'Tj' in stream_data:
                fixed = fix_content_stream_text(stream_data)
                return prefix + fixed + suffix
        
        return match.group(0)
    
    result = re.sub(stream_pattern, process_stream, pdf_bytes, flags=re.DOTALL)
    return result


def fix_pdf_rtl(pdf_bytes):
    """Fix RTL text in PDF using best available method"""
    if PIKEPDF_AVAILABLE:
        return fix_pdf_with_pikepdf(pdf_bytes)
    else:
        return fix_pdf_with_regex(pdf_bytes)


# =============================================================================
# PROGRESS TRACKER
# =============================================================================

class ProgressTracker:
    def __init__(self, job_id, output_folder):
        self.job_id = job_id
        self.progress_file = os.path.join(output_folder, f"progress_{job_id}.json") if job_id else None
    
    def update(self, step, progress, message):
        if not self.progress_file:
            return
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "job_id": self.job_id, "step": step, "progress": progress,
                    "message": message, "status": "processing",
                    "timestamp": datetime.now().isoformat()
                }, f, ensure_ascii=False)
        except:
            pass
    
    def complete(self, text_file, pdf_file, log_file, rtl_stats):
        if not self.progress_file:
            return
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                "job_id": self.job_id, "status": "completed", "progress": 100,
                "text_file": text_file, "pdf_file": pdf_file, "log_file": log_file,
                "rtl_stats": rtl_stats,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False)
    
    def error(self, msg):
        if not self.progress_file:
            return
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump({
                "job_id": self.job_id, "status": "error", "error": msg,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False)


# =============================================================================
# MAIN
# =============================================================================

def main():
    if len(sys.argv) == 4:
        pdf_path, output_folder, output_prefix = sys.argv[1:4]
        job_id = None
    elif len(sys.argv) == 5:
        pdf_path, output_folder, output_prefix, job_id = sys.argv[1:5]
    else:
        print(json.dumps({"error": "Usage: python script.py <pdf> <output_folder> <prefix> [job_id]"}))
        sys.exit(1)
    
    progress = ProgressTracker(job_id, output_folder)
    rtl_logger = RTLLogger()
    
    tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"
    languages = "eng+fas"
    dpi = 300
    
    try:
        progress.update("init", 5, "Initializing...")
        rtl_logger.log("OCR process started")
        rtl_logger.log(f"Input PDF: {pdf_path}")
        rtl_logger.log(f"Languages: {languages}")
        rtl_logger.log(f"DPI: {dpi}")
        
        os.makedirs(output_folder, exist_ok=True)
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Convert PDF to images
        progress.update("convert", 10, "Converting PDF...")
        rtl_logger.log("Converting PDF to images...")
        pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
        total = len(pages)
        rtl_logger.log(f"PDF has {total} pages")
        
        png_files = []
        for i, page in enumerate(pages):
            p = os.path.join(output_folder, f"{output_prefix}_p{i+1}.png")
            page.save(p, "PNG")
            png_files.append(p)
        
        # Extract text using HOCR with RTL markers
        progress.update("ocr", 25, "Extracting text with HOCR...")
        rtl_logger.log("Starting HOCR text extraction...")
        
        all_text = ""
        for i, png in enumerate(png_files):
            progress.update("ocr", 25 + (25*i/total), f"OCR page {i+1}/{total}")
            
            # Use HOCR extraction with RTL markers
            page_text = extract_text_with_hocr(png, languages, i+1, rtl_logger)
            all_text += f"\n\n--- Page {i+1} ---\n\n{page_text}"
        
        rtl_logger.log(f"Text extraction complete. {rtl_logger.lines_reversed} lines reversed")
        
        # Save text file
        text_path = os.path.join(output_folder, f"{output_prefix}.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(all_text)
        rtl_logger.log(f"Text saved to: {text_path}")
        
        # Save log file
        log_path = os.path.join(output_folder, f"{output_prefix}_rtl_log.txt")
        rtl_logger.write_log(log_path)
        
        # Create Tesseract PDFs
        progress.update("pdf", 55, "Creating PDFs...")
        rtl_logger.log("Creating searchable PDFs...")
        tess_pdfs = []
        for i, png in enumerate(png_files):
            progress.update("pdf", 55 + (15*i/total), f"PDF page {i+1}/{total}")
            tess_pdfs.append(pytesseract.image_to_pdf_or_hocr(Image.open(png), lang=languages, extension='pdf'))
        
        # Fix RTL in PDFs
        progress.update("fix", 75, "Fixing RTL text in PDF...")
        rtl_logger.log("Fixing RTL text in PDF streams...")
        fixed = []
        for i, pdf in enumerate(tess_pdfs):
            progress.update("fix", 75 + (10*i/total), f"Fixing page {i+1}/{total}")
            try:
                fixed.append(fix_pdf_rtl(pdf))
            except:
                fixed.append(pdf)
        
        # Merge PDFs
        progress.update("merge", 90, "Merging...")
        rtl_logger.log("Merging PDF pages...")
        pdf_out = os.path.join(output_folder, f"{output_prefix}.pdf")
        merger = PdfMerger()
        for f in fixed:
            merger.append(BytesIO(f))
        merger.write(pdf_out)
        merger.close()
        rtl_logger.log(f"PDF saved to: {pdf_out}")
        
        # Cleanup PNG files
        for p in png_files:
            if os.path.exists(p):
                os.remove(p)
        
        rtl_stats = rtl_logger.get_summary()
        progress.complete(text_path, pdf_out, log_path, rtl_stats)
        
        orig = os.path.getsize(pdf_path)
        out = os.path.getsize(pdf_out)
        
        print(json.dumps({
            "success": True,
            "text_file": text_path,
            "pdf_file": pdf_out,
            "log_file": log_path,
            "original_kb": round(orig/1024, 1),
            "output_kb": round(out/1024, 1),
            "ratio": round(out/orig, 2) if orig else 0,
            "method": "pikepdf" if PIKEPDF_AVAILABLE else "regex",
            "job_id": job_id,
            "rtl_stats": {
                "total_words": rtl_stats['total_words'],
                "rtl_words": rtl_stats['rtl_words'],
                "lines_reversed": rtl_stats['lines_reversed'],
                "rtl_percentage": rtl_stats['rtl_percentage']
            }
        }))
        
    except Exception as e:
        import traceback
        progress.error(str(e))
        rtl_logger.log(f"ERROR: {str(e)}")
        print(json.dumps({
            "success": False, "error": str(e),
            "traceback": traceback.format_exc(), "job_id": job_id
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()