#!/usr/bin/env python3

"""Test script for CMU AI Gateway API access."""

import os
import sys

import openai


def main():
    # Get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        print("\nUsage: export OPENAI_API_KEY='your_api_key'", file=sys.stderr)
        print("       python scripts/api_key_reference.py", file=sys.stderr)
        sys.exit(1)

    # Initialize OpenAI client with CMU AI Gateway
    # LiteLLM Proxy is OpenAI compatible
    # Read More: https://docs.litellm.ai/docs/proxy/user_keys
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://ai-gateway.andrew.cmu.edu/"
    )

    print("Testing CMU AI Gateway connection...")
    print("Model: gpt-4.1-mini")
    print("-" * 80)

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": "this is a test request, write a short poem"
                }
            ]
        )

        # Print formatted response
        print("\nResponse:")
        print(response.choices[0].message.content)
        print("-" * 80)
        print(f"Usage: {response.usage.total_tokens} tokens "
              f"(prompt: {response.usage.prompt_tokens}, "
              f"completion: {response.usage.completion_tokens})")
        print("✓ API connection successful!")

    except openai.AuthenticationError:
        print("Error: Invalid API key", file=sys.stderr)
        sys.exit(1)
    except openai.APIError as e:
        print(f"Error: API request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()