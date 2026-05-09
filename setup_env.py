import os
import yaml

def setup_env():
    env_file = ".env"
    config_file = "config.yaml"
    
    # 1. Handle .env file
    if os.path.exists(env_file):
        print(f"'{env_file}' already exists. Skipping creation.")
    else:
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

    # 2. Handle config.yaml file
    if os.path.exists(config_file):
        print(f"'{config_file}' already exists. Skipping creation.")
    else:
        config_content = {
            "openai": {
                "api_key": "${OPENAI_API_KEY}",
                "model": "${OPENAI_MODEL}",
                "api_base_url": "${OPENAI_API_BASE_URL}",
                "temperature": 0.0
            },
            "paths": {
                "system_prompt": "system_prompt.md"
            },
            "agent": {
                "max_iterations": 10
            }
        }
        try:
            with open(config_file, "w") as f:
                yaml.dump(config_content, f, default_flow_style=False)
            print(f"Successfully created '{config_file}'.")
        except Exception as e:
            print(f"An error occurred while creating the {config_file} file: {e}")

if __name__ == "__main__":
    setup_env()
