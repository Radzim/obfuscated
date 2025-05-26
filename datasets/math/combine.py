import os
import json

def combine_json_files(input_dir, output_file):
    combined = []
    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            path = os.path.join(input_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    combined.extend(data)
                else:
                    combined.append(data)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)

combine_json_files('math', 'math.json')