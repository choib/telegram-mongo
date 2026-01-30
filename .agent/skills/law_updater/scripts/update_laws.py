import os
import re
import requests
import unicodedata
from xml.etree import ElementTree as ET
from pdfminer.high_level import extract_text
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
from pdfminer.pdfpage import PDFPage
import io
import time

# Configuration
SOURCE_DIR = "/Users/bo/workspace/korean_law"
SEARCH_LIST_URL = "https://www.law.go.kr/lsScListR.do?menuId=1&subMenuId=15&tabMenuId=81"
XML_CONTENT_URL = "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq={}&viewCls=lsXml"
PDF_DOWNLOAD_URL = "https://www.law.go.kr/lsPdfPrint.do"

def normalize_name(name):
    return unicodedata.normalize('NFC', name)

def extract_law_name(filename):
    name = normalize_name(filename)
    name = os.path.splitext(name)[0]
    # Remove version, number, date info in parentheses
    name = re.sub(r'\(.*?\)', '', name).strip()
    return name

def get_law_info(law_name):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        data = {
            "q": law_name,
            "outmax": "5", # Reducing outmax for speed
            "p18": "0",
            "p19": "1,3",
            "pg": "1",
            "lsType": "null",
            "section": "lawNm",
            "lsiSeq": "0",
            "p9": "2,4"
        }
        response = requests.post(SEARCH_LIST_URL, headers=headers, data=data, timeout=10)
        if response.status_code == 200:
            html = response.text
            # Look for lsViewWideAll('282557','20251231', ...)
            match = re.search(r"lsViewWideAll\('(\d+)',\s*'(\d+)'", html)
            if match:
                lsi_seq = match.group(1)
                ef_yd = match.group(2)
                title_match = re.search(r'title="([^"]+)"', html)
                if title_match:
                    full_title = title_match.group(1).replace('\r', '').replace('\n', ' ').strip()
                    # Remove everything from the first [ or 시행
                    # Examples:
                    # '가사소송규칙 [시행 2019. 8. 2.] ...' -> '가사소송규칙'
                    # '가등기담보 등에 관한 법률[시행 2017. 3. 28.]' -> '가등기담보 등에 관한 법률'
                    # We look for '[' or ' 시행'
                    formal_name = re.split(r'\[|\s+시행', full_title)[0].strip()
                else:
                    formal_name = law_name
                return lsi_seq, ef_yd, formal_name
    except Exception as e:
        with open("update_laws.log", "a", encoding="utf-8") as log:
            log.write(f"{law_name}: ERROR (search) -> {e}\n")
    return None, None, None

def fetch_law_xml(lsi_seq):
    try:
        url = XML_CONTENT_URL.format(lsi_seq)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        pass
    return None

def parse_xml_to_text(xml_content):
    try:
        root = ET.fromstring(xml_content)
        lines = []
        title = root.find(".//법령명_한글")
        if title is not None:
            lines.append(f"[{title.text}]")
            lines.append("-" * 20)
        
        for jo in root.findall(".//조문단위"):
            jo_num = jo.find("조문번호")
            jo_title = jo.find("조문제목")
            jo_content = jo.find("조문내용")
            header = ""
            if jo_num is not None: header += f"제{jo_num.text}조 "
            if jo_title is not None: header += f"({jo_title.text}) "
            if header: lines.append(header.strip())
            if jo_content is not None and jo_content.text:
                lines.append(jo_content.text.strip())
            
            for hang in jo.findall(".//항"):
                hang_num = hang.find("항번호")
                hang_content = hang.find("항내용")
                if hang_content is not None and hang_content.text:
                    prefix = f"  {hang_num.text}. " if hang_num is not None else "  "
                    lines.append(f"{prefix}{hang_content.text.strip()}")
                for ho in hang.findall(".//호"):
                    ho_num = ho.find("호번호")
                    ho_content = ho.find("호내용")
                    if ho_content is not None and ho_content.text:
                        prefix = f"    {ho_num.text}. " if ho_num is not None else "    "
                        lines.append(f"{prefix}{ho_content.text.strip()}")
            lines.append("")
        return "\n".join(lines).strip()
    except:
        return None

def extract_text_with_margins(pdf_path, header_margin=775, footer_margin=90):
    """Extracts text from PDF while ignoring headers and footers based on coordinates."""
    try:
        fp = open(pdf_path, 'rb')
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        
        extracted_pages = []
        for page in PDFPage.get_pages(fp):
            interpreter.process_page(page)
            layout = device.get_result()
            
            page_text = []
            # Sort items by vertical position (top to bottom) then horizontal
            items = []
            for obj in layout:
                if isinstance(obj, (LTTextBox, LTTextLine)):
                    # y0 is bottom, y1 is top.
                    if obj.bbox[1] > footer_margin and obj.bbox[3] < header_margin:
                        items.append(obj)
            
            # Sort by y1 descending (top to bottom)
            items.sort(key=lambda x: x.bbox[3], reverse=True)
            for item in items:
                page_text.append(item.get_text().strip())
            
            extracted_pages.append("\n".join(page_text))
            
        fp.close()
        return "\n\n".join(extracted_pages).strip()
    except Exception as e:
        print(f"Error extracting with margins: {e}")
        return None

def download_pdf_and_convert(lsi_seq, ef_yd):
    try:
        # Check if we should use coordinate filtering (header/footer removal)
        # We'll use our new margin-aware function
        data = {'lsiSeq': lsi_seq, 'efYd': ef_yd, 'fileType': 'pdf', 'joAllCheck': 'Y', 'ancYnChk': '0'}
        response = requests.post(PDF_DOWNLOAD_URL, data=data, timeout=20)
        if response.status_code == 200:
            pdf_path = f"temp_{lsi_seq}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            # Use custom extraction to remove headers/footers
            text = extract_text_with_margins(pdf_path)
            
            # Fallback to standard extraction if custom fails
            if not text or len(text) < 100:
                text = extract_text(pdf_path)
                
            os.remove(pdf_path)
            return text
    except:
        pass
    return None

def update_law(law_name, old_filenames):
    print(f"Updating {law_name}...")
    lsi_seq, ef_yd, formal_name = get_law_info(law_name)
    if not lsi_seq:
        print(f"  FAILED: Could not find latest version.")
        return False
    
    content = None
    method = "XML"
    xml_content = fetch_law_xml(lsi_seq)
    if xml_content:
        content = parse_xml_to_text(xml_content)
    
    if not content or len(content) < 200:
        method = "PDF"
        content = download_pdf_and_convert(lsi_seq, ef_yd)
    
    if content and len(content) >= 200:
        # Success!
        # 1. Delete old files for this EXACT lsi_seq
        # We look for files containing (lsi_seq) to avoid clashing with laws of the same name
        for f in os.listdir(SOURCE_DIR):
            if f"({lsi_seq})" in f:
                old_path = os.path.join(SOURCE_DIR, f)
                if os.path.exists(old_path):
                    os.remove(old_path)
        
        # (Transition) Also delete files matching the old pattern: LawName(Date).txt
        # to ensure we don't end up with duplicates during the naming convention change.
        escaped_name = re.escape(law_name)
        old_pattern = re.compile(rf"^{escaped_name}\(\d{{8}}\)\.txt$", re.IGNORECASE)
        for f in os.listdir(SOURCE_DIR):
            if old_pattern.match(f):
                old_path = os.path.join(SOURCE_DIR, f)
                if os.path.exists(old_path):
                    os.remove(old_path)
        
        # 2. Save new file
        # Format name for safety: remove newlines and illegal FS characters
        clean_formal = formal_name.replace('\n', ' ').replace('\r', ' ').strip()
        safe_name = re.sub(r'[\\/*?:"<>|]', "", clean_formal)
        new_filename = f"{safe_name}({lsi_seq})({ef_yd}).txt"
        new_path = os.path.join(SOURCE_DIR, new_filename)
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        msg = f"  SUCCESS: Updated via {method} -> {new_filename}"
        print(msg, flush=True)
        with open("update_laws.log", "a", encoding="utf-8") as log:
            log.write(f"{law_name}: SUCCESS ({method}) -> {new_filename}\n")
        return True
    
    msg = f"  FAILED: Could not retrieve content."
    print(msg, flush=True)
    with open("update_laws.log", "a", encoding="utf-8") as log:
        log.write(f"{law_name}: FAILED (retrieval)\n")
    return False

def main():
    if not os.path.exists(SOURCE_DIR): return
    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith('.txt')]
    
    # Group old files by law name
    law_to_files = {}
    for f in files:
        name = extract_law_name(f)
        if name not in law_to_files:
            law_to_files[name] = []
        law_to_files[name].append(f)
    
    # If law_names.txt exists, use it to ensure we hit deleted laws
    # If law_names.txt exists in the same directory, use it
    script_dir = os.path.dirname(os.path.abspath(__file__))
    names_file = os.path.join(script_dir, "law_names.txt")
    if os.path.exists(names_file):
        with open(names_file, 'r', encoding='utf-8') as f:
            sorted_names = [line.strip() for line in f if line.strip()]
    else:
        sorted_names = sorted([n for n in law_to_files.keys() if len(n) > 1])
    
    print(f"Processing {len(sorted_names)} laws...", flush=True)
    
    results = []
    for name in sorted_names:
        success = update_law(name, law_to_files.get(name, []))
        results.append(success)
        time.sleep(0.5)
    
    print(f"\nFinal Report: {sum(results)}/{len(results)} updated successfully.")

if __name__ == "__main__":
    main()
