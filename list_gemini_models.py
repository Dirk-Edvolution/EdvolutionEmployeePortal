#!/usr/bin/env python3
"""
List available Gemini models
"""
import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import google.generativeai as genai
from backend.config.settings import GOOGLE_API_KEY

def main():
    print("=" * 60)
    print("LISTING AVAILABLE GEMINI MODELS")
    print("=" * 60)
    print()

    if not GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY not configured")
        return

    genai.configure(api_key=GOOGLE_API_KEY)

    print("Available models:")
    print("-" * 60)
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  {model.name}")
            print(f"    Display Name: {model.display_name}")
            print(f"    Supported Methods: {model.supported_generation_methods}")
            print()

if __name__ == "__main__":
    main()
