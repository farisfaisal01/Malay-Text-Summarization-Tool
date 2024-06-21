from io import BytesIO
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import utils
from docx import Document

def export_pdf(text, date):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    margin = inch
    text_width = width - 2 * margin
    textobject = p.beginText(margin, height - margin)
    textobject.setFont("Helvetica", 12)
    textobject.textLines(wrap_text(f"Summary Date: {date}\nSummary Content:\n{text}", text_width))
    p.drawText(textobject)
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='summary.pdf', mimetype='application/pdf')

def wrap_text(text, max_width):
    lines = text.splitlines()
    wrapped_lines = []
    for line in lines:
        wrapped_lines.extend(utils.simpleSplit(line, "Helvetica", 12, max_width))
    return wrapped_lines

def export_word(text, date):
    buffer = BytesIO()
    doc = Document()
    doc.add_heading('Summary Details', level=1)
    doc.add_paragraph(f"Summary Date: {date}")
    doc.add_paragraph("Summary Content:")
    doc.add_paragraph(text)
    doc.save(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='summary.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

def export_txt(text, date):
    buffer = BytesIO()
    content = f"Summary Date: {date}\nSummary Content:\n{text}"
    buffer.write(content.encode('utf-8'))
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='summary.txt', mimetype='text/plain')
