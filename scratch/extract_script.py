import json
import os

log_path = r'C:\Users\Vivek\.gemini\antigravity\brain\e767e6a5-4033-4910-b413-088b0eeb085b\.system_generated\logs\overview.txt'

with open(log_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    # Line 67 (index 66)
    target_line = lines[66]
    data = json.loads(target_line)
    content = data.get('content', '')
    
    # Save the extracted content to a file
    with open('extracted_script.js', 'w', encoding='utf-8') as out:
        out.write(content)

print("Extracted script to extracted_script.js")
