from openpyxl.styles import Font

from reportlab.pdfgen import canvas
from docx import Document
from openpyxl import Workbook
import os
from fpdf import FPDF

def generate_document(content: str, file_type: str):
    OUTPUT_DIR = "generated"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filename = os.path.join(
        OUTPUT_DIR,
        f"generated_file.{file_type}"
    )
    
    # Remove existing file if it exists to avoid permission errors
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except OSError:
            pass

    def parse_bold_segments(text: str):
        segments = []
        index = 0
        while index < len(text):
            if text.startswith("**", index):
                end_index = text.find("**", index + 2)
                if end_index == -1:
                    segments.append((text[index:], False))
                    break
                bold_text = text[index + 2:end_index]
                segments.append((bold_text, True))
                index = end_index + 2
            else:
                next_bold = text.find("**", index)
                if next_bold == -1:
                    segments.append((text[index:], False))
                    break
                segments.append((text[index:next_bold], False))
                index = next_bold
        return segments

    # if file_type == "pdf":
    #     c = canvas.Canvas(filename)

    #     y = 800
    #     for line in content.split("\n"):
    #         c.drawString(50, y, line[:100])
    #         y -= 20

    #     c.save()
    
    if file_type == "pdf":
        #filename = f"generated_file.pdf"
        pdf = FPDF()

        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        lines = str(content).split("\n")
        for line in lines:
            if line.strip() == "":
                pdf.ln(10)
                continue

            segments = parse_bold_segments(line)
            for segment_text, is_bold in segments:
                pdf.set_font("Arial", style="B" if is_bold else "", size=12)
                pdf.write(10, segment_text)
            pdf.ln(10)
        try:
            pdf.output(filename)
        except Exception as e:
            return {
                "error": str(e)
        }
        #pdf.output(filename)
        

    elif file_type == "docx":
        doc = Document()

        for line in content.split("\n"):
            paragraph = doc.add_paragraph()
            segments = parse_bold_segments(line)
            for segment_text, is_bold in segments:
                run = paragraph.add_run(segment_text)
                if is_bold:
                    run.bold = True

        doc.save(filename)

    elif file_type == "xlsx":
        wb = Workbook()
        ws = wb.active

        row_num = 1

        for line in content.splitlines():

            line = line.strip()

            if not line:
                continue

            # Markdown Table
            if "|" in line and line.startswith("|") and line.endswith("|"):
                cells = [cell.strip() for cell in line.strip("|").split("|")]

                # Skip separator row
                if all(set(cell) <= {"-"} for cell in cells):
                    continue

                for col_num, value in enumerate(cells, start=1):
                    cell = ws.cell(row=row_num, column=col_num)
                    cell.value = value

                    if row_num == 1:
                        cell.font = Font(bold=True)

                row_num += 1

            # Regular text
            else:
                ws.cell(row=row_num, column=1, value=line)
                row_num += 1

        wb.save(filename)

    else:
        return {"error": "Unsupported file type"}

    print("Saved:", os.path.abspath(filename))
    
    return {
        "message": f"{file_type.upper()} Generated Successfully",
        "file_path": os.path.abspath(filename)
    }