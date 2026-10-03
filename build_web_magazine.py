import re
import os

def build_interactive_magazine():
    input_file = "Complete_Magazine_Draft.md"
    output_file = "index.html"
    
    if not os.path.exists(input_file):
        print("Error: Draft file not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Parse sections and articles manually to wrap them in stunning UI components
    # We will use simple regex to find all ### Articles
    
    html_head = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Indian Army Northeast Report</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-color: #0b0f12;
                --card-bg: #151a1f;
                --text-main: #e2e8f0;
                --text-muted: #94a3b8;
                --accent-olive: #4d5d53;
                --accent-saffron: #f59e0b;
                --accent-blue: #3b82f6;
            }
            body {
                margin: 0;
                padding: 0;
                background-color: var(--bg-color);
                color: var(--text-main);
                font-family: 'Inter', sans-serif;
                line-height: 1.6;
                overflow-x: hidden;
            }
            /* Premium Cover Section */
            .cover {
                height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                background: linear-gradient(135deg, rgba(11,15,18,0.9) 0%, rgba(21,26,31,0.95) 100%), url('https://images.unsplash.com/photo-1544253303-62c16260a92f?q=80&w=2070') center/cover;
                text-align: center;
                padding: 0 20px;
                border-bottom: 4px solid var(--accent-saffron);
                animation: fadeIn 2s ease-out;
            }
            .cover h1 {
                font-family: 'Playfair Display', serif;
                font-size: 5rem;
                font-weight: 900;
                margin: 0;
                background: -webkit-linear-gradient(#fff, #94a3b8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: -2px;
            }
            .cover p {
                font-size: 1.5rem;
                color: var(--accent-saffron);
                text-transform: uppercase;
                letter-spacing: 4px;
                margin-top: 10px;
            }
            /* Layout */
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 60px 20px;
            }
            .section-title {
                font-family: 'Playfair Display', serif;
                font-size: 3rem;
                color: #fff;
                border-left: 6px solid var(--accent-saffron);
                padding-left: 20px;
                margin: 80px 0 40px 0;
            }
            /* Dynamic Grid */
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
                gap: 40px;
            }
            /* Glassmorphism Cards */
            .card {
                background: var(--card-bg);
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 16px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                backdrop-filter: blur(10px);
            }
            .card:hover {
                transform: translateY(-10px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.8);
                border-color: rgba(245, 158, 11, 0.3); /* Saffron glow */
            }
            .card h3 {
                font-size: 1.4rem;
                color: #fff;
                margin-top: 0;
                line-height: 1.4;
            }
            .card p {
                font-size: 1.05rem;
                color: var(--text-muted);
            }
            .citation {
                margin-top: 20px;
                font-size: 0.85rem;
                color: var(--accent-saffron);
                font-weight: 700;
                border-top: 1px solid rgba(255,255,255,0.1);
                padding-top: 15px;
            }
            .citation a {
                color: var(--accent-blue);
                text-decoration: none;
            }
            /* Table Styling for Appendices */
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 30px;
                background: var(--card-bg);
                border-radius: 12px;
                overflow: hidden;
            }
            th, td {
                padding: 15px 20px;
                text-align: left;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
            th {
                background: rgba(0,0,0,0.4);
                color: var(--accent-saffron);
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            tr:hover {
                background: rgba(255,255,255,0.02);
            }
            /* Animations */
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
        </style>
    </head>
    <body>
        <div class="cover">
            <h1>INDIAN ARMY IN THE NORTHEAST</h1>
            <p>Security, Development, and Youth Empowerment</p>
        </div>
        <div class="container">
    """

    # We will import markdown module to parse the raw text blocks safely
    import markdown
    
    # Strip Gemini Prompts
    md_text = re.sub(r'\*\(Prompt for Gemini Canvas:.*?\)\*', '', md_text, flags=re.DOTALL)
    
    # Process sections
    sections = md_text.split('## ')
    
    html_content = ""
    for sec in sections[1:]:
        lines = sec.split('\n')
        section_name = lines[0].strip()
        html_content += f'<h2 class="section-title">{section_name}</h2>\n<div class="grid">\n'
        
        # If this is a back matter/appendix section with tables
        if "BACK MATTER" in section_name or "Appendix" in sec:
            html_content += '</div>' # close grid
            # parse the rest as pure markdown (tables)
            rest_md = "\n".join(lines[1:])
            html_content += markdown.markdown(rest_md, extensions=['tables'])
            continue
            
        # Extract articles
        articles = sec.split('### ')
        
        # If it has front matter list, render it normally outside grid
        if len(articles) == 1:
            html_content += '</div>'
            html_content += markdown.markdown("\n".join(lines[1:]))
            continue
            
        for article in articles[1:]:
            art_lines = article.split('\n')
            title = art_lines[0].strip()
            
            body = []
            citation = ""
            for line in art_lines[1:]:
                if line.startswith('> (Source:'):
                    citation = line.replace('> ', '')
                elif line.strip() != '---' and line.strip() != '':
                    body.append(line.strip())
            
            body_text = "<br><br>".join(body)
            
            # Link formatting in citation
            citation = re.sub(r'\[Link\]\((.*?)\)', r'<a href="\1" target="_blank">[Link]</a>', citation)
            
            html_content += f"""
            <div class="card">
                <h3>{title}</h3>
                <p>{body_text}</p>
                <div class="citation">{citation}</div>
            </div>
            """
            
        html_content += '</div>\n' # close grid
        
    html_footer = """
        </div>
    </body>
    </html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_head + html_content + html_footer)
        
    print(f"Ultra-Premium Interactive Web Magazine generated at {output_file}")

if __name__ == "__main__":
    build_interactive_magazine()
