import os
from dotenv import load_dotenv
from openai import OpenAI

print("Attempting to initialize OpenAI client...")

try:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables or .env file.")
    else:
        print(f"Found OPENAI_API_KEY: {api_key[:5]}...{api_key[-4:]}") # Print partial key for confirmation
        
        # Simplest client initialization
        client = OpenAI(api_key=api_key)
        print("OpenAI client initialized successfully!")
        
        # Optional: Make a simple test call (e.g., list models if your key has perms)
        # try:
        #     models = client.models.list()
        #     print("Successfully listed models.")
        #     # print(list(models))
        # except Exception as e_call:
        #     print(f"Error making test call to OpenAI: {e_call}")

except Exception as e_init:
    print(f"ERROR initializing OpenAI client: {e_init}")
    import traceback
    traceback.print_exc() 