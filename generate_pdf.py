import markdown
from weasyprint import HTML, CSS
import re

def generate():
    with open('Complete_Magazine_Draft.md', 'r', encoding='utf-8') as f:
        text = f.read()
        
    # Clean up the AI prompts and meta text
    text = re.sub(r'\*\(Prompt for Gemini Canvas:.*?\)\*', '', text, flags=re.DOTALL)
    text = text.replace("*Ready to be copy-pasted into Canva/InDesign*", "")
    
    html_content = markdown.markdown(text, extensions=['tables'])
    
    # Military themed CSS for the PDF
    css = """
    @page {
        size: A4;
        margin: 2.54cm; /* 1 inch margins */
        @bottom-right {
            content: counter(page);
            font-family: 'Helvetica', sans-serif;
            font-size: 10pt;
            color: #666;
        }
    }
    body {
        font-family: 'Georgia', serif;
        font-size: 11pt;
        line-height: 1.5;
        color: #222;
    }
    h1 {
        font-family: 'Helvetica', sans-serif;
        font-size: 36pt;
        color: #4B5320; /* Army Green */
        text-align: center;
        margin-top: 40%;
        text-transform: uppercase;
        page-break-after: always;
    }
    h2 {
        font-family: 'Helvetica', sans-serif;
        font-size: 22pt;
        color: #000080; /* Navy Blue */
        border-bottom: 3px solid #FF9933; /* Saffron Accent */
        padding-bottom: 5px;
        page-break-before: always;
        margin-top: 0;
    }
    h3 {
        font-family: 'Helvetica', sans-serif;
        font-size: 14pt;
        color: #4B5320;
        margin-top: 25px;
        margin-bottom: 10px;
    }
    p {
        text-align: justify;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        margin-bottom: 20px;
        font-size: 10pt;
    }
    th, td {
        border: 1px solid #ccc;
        padding: 10px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
        font-family: 'Helvetica', sans-serif;
        color: #000080;
    }
    blockquote {
        font-style: italic;
        color: #555;
        border-left: 4px solid #4B5320;
        margin-left: 0;
        padding-left: 15px;
        font-size: 9.5pt;
        background-color: #f9f9f9;
        padding-top: 5px;
        padding-bottom: 5px;
    }
    hr {
        border: 0;
        border-top: 1px solid #ddd;
        margin: 30px 0;
    }
    """
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    print("Rendering PDF...")
    HTML(string=full_html).write_pdf('Indian_Army_Northeast_Magazine.pdf', stylesheets=[CSS(string=css)])
    print("PDF successfully generated!")

if __name__ == "__main__":
    generate()
