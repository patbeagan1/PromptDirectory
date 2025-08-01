#!/usr/bin/env python

import sys

import requests


def run_ollama_prompt(prompt: str):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "gemma",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }
    try:
        print("Running with Ollama...", file=sys.stderr)
        response = requests.post(url, json=data)
        response.raise_for_status()
        response_data = response.json()

        if 'response' not in response_data:
            raise ValueError("Ollama API response is missing the 'response' key.")
        print(response_data['response'].strip())

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama: {e}", file=sys.stderr)
        print("Please ensure Ollama is running and the 'llama3' model is available.", file=sys.stderr)


def execute_prompt(prompt: str, model: str = "gemma") -> str:
    url = "http://localhost:11434/api/generate"

    data = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    try:
        print("Running with Ollama...", file=sys.stderr)
        response = requests.post(url, json=data)
        response.raise_for_status()
        response_data = response.json()

        if 'response' not in response_data:
            raise ValueError("Ollama API response is missing the 'response' key.")

        return response_data['response'].strip()

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama: {e}", file=sys.stderr)
        print("Please ensure Ollama is running and the 'llama3' model is available.", file=sys.stderr)
