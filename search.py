import re
import subprocess
from pathlib import Path
ROOT_DIR = str(Path.home() / 'Documents')

def simple_search(query):
    cmd = ['tracker3', 'search', query]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    result = result.stdout.decode('utf-8')
    # Check to ensure that the results were returned.
    if not result.startswith("Results:\n"):
        return
    result = result[9:]
    # split output by lines and remove duplicates by converting to set
    unique_results = set(result.split("\n\n"))
    location = f"file://{ROOT_DIR}"
    # Process each item to remove special characters from the first line
    processed_results = set()
    for item in unique_results:
        lines = str(item).strip().split('\n')
        if lines:
            # Remove special characters from the first line
            lines[0] = re.sub(r'\x1b[^m]*m', '', lines[0])
            if lines[0].startswith(location):
                processed_results.add('\n'.join(lines))
    return processed_results

unique_results = simple_search('crypto')

for res in unique_results:
    print(res)
