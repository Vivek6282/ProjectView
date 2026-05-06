import subprocess
import os
import time

def generate_pdf():
    # Paths
    html_file = os.path.abspath("ai.html")
    output_pdf = os.path.abspath("AI_Exam_Answer_Sheet.pdf")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    start_time = time.time()
    print(f"Initializing Fast PDF Generation...")
    
    # Command to run Edge in headless mode for high-fidelity PDF printing
    command = [
        edge_path,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--disable-extensions",
        f"--print-to-pdf={output_pdf}",
        "--virtual-time-budget=1500", # Optimized wait time
        f"file:///{html_file}"
    ]

    try:
        subprocess.run(command, check=True, capture_output=True)
        end_time = time.time()
        print(f"Success! PDF created in {end_time - start_time:.2f} seconds.")
        print(f"Location: {output_pdf}")
    except Exception as e:
        print(f"Error generating PDF: {e}")

if __name__ == "__main__":
    generate_pdf()
