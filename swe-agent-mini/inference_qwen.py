#!/usr/bin/env python3
"""
Simple script to perform inference with Qwen model on AWS Bedrock
"""

import boto3
import json

# AWS credentials from code-gen_accessKeys.csv
AWS_ACCESS_KEY_ID = "***"
AWS_SECRET_ACCESS_KEY = "***"
AWS_REGION = "us-east-1"

# Model ID
MODEL_ID = "qwen.qwen3-coder-30b-a3b-v1:0"

def create_bedrock_client():
    """Create and return a Bedrock Runtime client"""
    return boto3.client(
        service_name='bedrock-runtime',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

def invoke_model(prompt, max_tokens=512, temperature=0.7):
    """
    Invoke the Qwen model with the given prompt

    Args:
        prompt: The input text prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0-1)

    Returns:
        Generated text response
    """
    client = create_bedrock_client()

    # Prepare the request body
    request_body = {
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9
    }

    try:
        # Invoke the model
        response = client.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )

        # Parse the response
        response_body = json.loads(response['body'].read())

        # Extract the generated text from ChatCompletion format
        generated_text = response_body['choices'][0]['message']['content']

        return generated_text

    except Exception as e:
        print(f"Error invoking model: {e}")
        return None

def main():
    """Main function to demonstrate the inference"""
    # Example prompt
    prompt = "Write a Python function to calculate the factorial of a number."

    print(f"Prompt: {prompt}\n")
    print("Generating response...\n")

    response = invoke_model(prompt)

    if response:
        print("Response:")
        print(response)
    else:
        print("Failed to get response from the model")

if __name__ == "__main__":
    main()
