#!/usr/bin/env python3

"""Test script to verify all 3 models are working correctly."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from litellm import completion


def test_model(model_name: str, api_base: str = None) -> bool:
    """Test a single model with a simple coding prompt."""
    print(f"\n{'='*80}")
    print(f"Testing: {model_name}")
    print(f"{'='*80}")

    try:
        # Simple test prompt
        messages = [
            {
                "role": "system",
                "content": "You are a helpful coding assistant."
            },
            {
                "role": "user",
                "content": "Write a Python function that adds two numbers and returns the result."
            }
        ]

        kwargs = {
            "model": model_name,
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.0,
        }

        if api_base:
            kwargs["api_base"] = api_base

        print(f"Sending request to {model_name}...")
        response = completion(**kwargs)

        content = response.choices[0].message.content
        print(f"\n✅ SUCCESS - Model responded:")
        print("-" * 80)
        print(content[:300] + ("..." if len(content) > 300 else ""))
        print("-" * 80)
        print(f"Tokens used: {response.usage.total_tokens}")

        return True

    except Exception as e:
        print(f"\n❌ FAILED - Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Test all three models."""
    print("="*80)
    print("Model Inference Test")
    print("="*80)
    print("\nThis script tests if all 3 models can be accessed via LiteLLM.")
    print("Make sure you have started the model servers before running this.")
    print()

    # Configuration for each model
    # Adjust these based on your actual server setup
    models = [
        {
            "name": "qwen3-coder",
            "endpoint": "http://localhost:8000/v1",
            "model_id": "Qwen/Qwen3-Coder-30B-A3B-Instruct"
        },
        {
            "name": "devstral",
            "endpoint": "http://localhost:8001/v1",
            "model_id": "mistralai/Devstral-Small-2507"
        },
        {
            "name": "cwm",
            "endpoint": "http://localhost:8002/v1",
            "model_id": "facebook/cwm"
        }
    ]

    results = {}

    for model_config in models:
        # Test with openai/ prefix for LiteLLM
        model_str = f"openai/{model_config['name']}"
        success = test_model(
            model_name=model_str,
            api_base=model_config["endpoint"]
        )
        results[model_config["name"]] = success

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name:20s} {status}")

    print("="*80)

    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All models are working correctly!")
        return 0
    else:
        print("\n⚠️  Some models failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
