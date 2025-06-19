#!/bin/bash
# E2E Test Runner for GUTAI

echo "🚀 Running GUTAI End-to-End Test Suite"
echo "======================================="

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run the E2E test
echo "🧪 Starting E2E test workflow..."
python3 test_e2e.py

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ E2E Test completed successfully!"
else
    echo "❌ E2E Test failed!"
fi

exit $exit_code
