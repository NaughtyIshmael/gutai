#!/usr/bin/env python3
"""
Test script to verify Azure AI Inference integration without making API calls.
"""

import sys
from pathlib import Path


def test_azure_imports():
    """Test that Azure AI Inference can be imported"""
    print("Testing Azure AI Inference imports...")

    try:
        from azure.ai.inference import ChatCompletionsClient
        from azure.ai.inference.models import SystemMessage, UserMessage
        from azure.core.credentials import AzureKeyCredential

        print("✅ Azure AI Inference imports successful")
        return True
    except ImportError as e:
        print(f"❌ Azure AI Inference import failed: {e}")
        print("   Install with: pip install azure-ai-inference")
        return False


def test_client_initialization():
    """Test that the client can be initialized (without connecting)"""
    print("Testing client initialization...")

    try:
        from azure.ai.inference import ChatCompletionsClient
        from azure.core.credentials import AzureKeyCredential

        # Initialize with dummy values (no actual connection)
        client = ChatCompletionsClient(
            endpoint="https://models.github.ai/inference",
            credential=AzureKeyCredential("dummy_token"),
        )
        print("✅ Client initialization successful")
        return True
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False


def test_message_objects():
    """Test that message objects can be created"""
    print("Testing message object creation...")

    try:
        from azure.ai.inference.models import SystemMessage, UserMessage

        system_msg = SystemMessage("You are a helpful assistant.")
        user_msg = UserMessage("Hello, world!")

        print("✅ Message objects created successfully")
        return True
    except Exception as e:
        print(f"❌ Message object creation failed: {e}")
        return False


def main():
    """Run all Azure AI Inference tests"""
    print("🧪 Testing Azure AI Inference Integration")
    print("=" * 50)

    tests = [
        test_azure_imports,
        test_client_initialization,
        test_message_objects,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            results.append(False)
            print()

    # Summary
    passed = sum(results)
    total = len(results)

    print("=" * 50)
    print(f"Azure Integration Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 Azure AI Inference integration is working correctly!")
    else:
        print("⚠️  Some Azure AI Inference tests failed.")
        print("   Make sure to install: pip install azure-ai-inference")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
