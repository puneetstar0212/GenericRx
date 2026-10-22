import markdown
import os
from xhtml2pdf import pisa

def convert_md_to_pdf(md_filepath, pdf_filepath):
    # 1. Read Markdown file
    with open(md_filepath, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # 2. Convert Markdown to HTML
    html_body = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'toc'])
    
    # 3. Create a complete HTML document with some basic styling
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: a4 portrait;
                margin: 2cm;
                @frame footer {{
                    -pdf-frame-content: footerContent;
                    bottom: 1cm;
                    margin-left: 2cm;
                    margin-right: 2cm;
                    height: 1cm;
                }}
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #333333;
            }}
            h1 {{ color: #0d9488; font-size: 24pt; border-bottom: 2px solid #0d9488; padding-bottom: 5px; }}
            h2 {{ color: #115e59; font-size: 18pt; margin-top: 20px; border-bottom: 1px solid #e5e7eb; }}
            h3 {{ color: #0f766e; font-size: 14pt; }}
            p {{ margin-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; }}
            th {{ background-color: #f1f5f9; font-weight: bold; }}
            code {{ background-color: #f1f5f9; padding: 2px 4px; border-radius: 4px; font-family: monospace; font-size: 10pt; }}
            pre {{ background-color: #f1f5f9; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 10pt; }}
        </style>
    </head>
    <body>
        <div id="footerContent" style="text-align: right; font-size: 9pt; color: #64748b;">
            Page <pdf:pagenumber> of <pdf:pagecount>
        </div>
        {html_body}
    </body>
    </html>
    """

    # 4. Generate PDF
    with open(pdf_filepath, 'wb') as pdf_file:
        pisa_status = pisa.CreatePDF(
            src=html_content,
            dest=pdf_file,
            encoding='utf-8'
        )
    
    if pisa_status.err:
        print("Error generating PDF:", pisa_status.err)
    else:
        print(f"Successfully generated PDF at {pdf_filepath}")

if __name__ == "__main__":
    report_path = r"C:\Users\punee\.gemini\antigravity\brain\6fcf579e-b3b7-4c06-b49b-906724e6075a\project_report.md"
    output_path = os.path.join(os.path.dirname(__file__), "GenericRx_Project_Report.pdf")
    convert_md_to_pdf(report_path, output_path)
