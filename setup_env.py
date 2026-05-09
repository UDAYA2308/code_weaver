import os
import yaml

def setup_env():
    config_file = "config.yaml"
    
    # Handle config.yaml file
    if os.path.exists(config_file):
        print(f"'{config_file}' already exists. Skipping creation.")
    else:
        config_content = {
            "openai": {
                "api_key": "your_api_key_here",
                "model": "gpt-4o",
                "api_base_url": "https://api.openai.com/v1",
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
            print(f"Successfully created '{config_file}'. Please open it and add your API key.")
        except Exception as e:
            print(f"An error occurred while creating the {config_file} file: {e}")

if __name__ == "__main__":
    setup_env()
