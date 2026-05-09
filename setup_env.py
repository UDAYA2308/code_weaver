import os

def setup_env():
    env_file = ".env"
    
    if os.path.exists(env_file):
        print(f"'{env_file}' already exists. Skipping creation.")
        return

    # Default template for the .env file
    env_content = (
        "# OpenAI API Configuration\n"
        "OPENAI_API_KEY=your_api_key_here\n"
        "OPENAI_MODEL=gpt-4o\n"
        "OPENAI_API_BASE_URL=https://api.openai.com/v1\n"
    )

    try:
        with open(env_file, "w") as f:
            f.write(env_content)
        print(f"Successfully created '{env_file}'. Please open it and add your API key.")
    except Exception as e:
        print(f"An error occurred while creating the .env file: {e}")

if __name__ == "__main__":
    setup_env()
