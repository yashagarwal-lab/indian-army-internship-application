import os

def compile_magazine():
    final_file = "Complete_Magazine_Draft.md"
    
    with open(final_file, "w", encoding="utf-8") as out:
        # 1. Front Matter
        out.write("# INDIAN ARMY IN THE NORTHEAST: A COMPREHENSIVE REPORT\n\n")
        out.write("*(Prompt for Gemini Canvas: Please use this entire document to generate a 50-page magazine layout. Follow the exact page allocations and sections provided below, maintaining a formal military/development tone. Ensure it looks like a professional print magazine.)*\n\n")
        
        out.write("## FRONT MATTER (Pages 1-4)\n")
        out.write("- **Page 1:** Cover Page (Title: Indian Army in the Northeast - Security, Development, and Youth Empowerment)\n")
        out.write("- **Page 2:** Table of Contents\n")
        out.write("- **Page 3:** Editor’s Note / Introduction\n")
        out.write("- **Page 4:** Brief overview of the Indian Army in the NE\n\n")
        out.write("---\n\n")
        
        # 2. Main Content
        if os.path.exists("Final_Magazine_Content.md"):
            with open("Final_Magazine_Content.md", "r", encoding="utf-8") as f:
                content = f.read()
                # Replace the top header so it flows better
                content = content.replace("# Final Magazine Content Template\n\n*Ready to be copy-pasted into Canva/InDesign*\n\n", "")
                out.write(content)
                out.write("\n\n---\n\n")
                
        # 3. Back Matter
        out.write("## BACK MATTER (Pages 46-50)\n\n")
        out.write("*(Prompt for Gemini Canvas: Format the following two appendices as clean, professional tables on pages 46-49.)*\n\n")
        
        if os.path.exists("Appendix_1_Sources.md"):
            with open("Appendix_1_Sources.md", "r", encoding="utf-8") as f:
                out.write(f.read())
                out.write("\n\n")
                
        if os.path.exists("Appendix_2_Reasoning.md"):
            with open("Appendix_2_Reasoning.md", "r", encoding="utf-8") as f:
                out.write(f.read())
                out.write("\n\n")
                
        out.write("---\n")
        out.write("- **Page 50:** Back Cover (Closing image and institutional logo placeholders)\n")
        
    print(f"Successfully compiled everything into {final_file}")

if __name__ == "__main__":
    compile_magazine()
