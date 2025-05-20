import json
import sys

input_file = "fine_tuning_data.jsonl"
output_file_messages = "fine_tuning_clean_messages.jsonl"
output_file_prompt = "fine_tuning_clean_prompt.jsonl"

valid_lines_messages = []
valid_lines_prompt = []
errors = []

# Process each line
with open(input_file, 'r') as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:  # Skip empty lines
            continue
            
        try:
            # Parse JSON
            obj = json.loads(line)
            
            # Save messages format
            valid_lines_messages.append(json.dumps(obj))
            
            # Transform to prompt/completion format
            if 'messages' in obj:
                user_message = next((msg for msg in obj['messages'] if msg['role'] == 'user'), None)
                assistant_message = next((msg for msg in obj['messages'] if msg['role'] == 'assistant'), None)
                
                if user_message and assistant_message:
                    prompt_completion = {
                        "prompt": user_message['content'],
                        "completion": assistant_message['content']
                    }
                    valid_lines_prompt.append(json.dumps(prompt_completion))
        except json.JSONDecodeError as e:
            errors.append(f"Error on line {i}: {str(e)[:100]} - line content: {line[:50]}...")

# Write messages format to file
if valid_lines_messages:
    with open(output_file_messages, 'w') as f:
        for line in valid_lines_messages:
            f.write(line + '\n')
    print(f"Wrote {len(valid_lines_messages)} valid lines to {output_file_messages}")

# Write prompt/completion format to file
if valid_lines_prompt:
    with open(output_file_prompt, 'w') as f:
        for line in valid_lines_prompt:
            f.write(line + '\n')
    print(f"Wrote {len(valid_lines_prompt)} valid lines to {output_file_prompt}")

# Report errors
if errors:
    print(f"Found {len(errors)} errors:")
    for error in errors:
        print(error)
else:
    print("No errors found.")

# Verify the output files
try:
    with open(output_file_messages, 'r') as f:
        for i, line in enumerate(f, 1):
            json.loads(line)
    print(f"Verification successful: {output_file_messages} contains valid JSON on each line.")
except json.JSONDecodeError as e:
    print(f"Verification failed for {output_file_messages}: {str(e)}")

try:
    with open(output_file_prompt, 'r') as f:
        for i, line in enumerate(f, 1):
            json.loads(line)
    print(f"Verification successful: {output_file_prompt} contains valid JSON on each line.")
except json.JSONDecodeError as e:
    print(f"Verification failed for {output_file_prompt}: {str(e)}") 