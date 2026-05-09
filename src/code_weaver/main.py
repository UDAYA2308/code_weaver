import os
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    print("Code Weaver is now in chat-only mode.")
    print("To start chatting, run: python -m src.code_weaver.chat")

if __name__ == "__main__":
    main()
