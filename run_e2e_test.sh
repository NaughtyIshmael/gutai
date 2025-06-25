#!/bin/bash
# E2E Test Runner for GUTAI

# Parse command line arguments
LANGUAGE=${1:-"python"}  # Default to python if no argument provided

case $LANGUAGE in
    "python")
        echo "🚀 Running GUTAI Python End-to-End Test Suite"
        echo "=============================================="
        ;;
    "go"|"golang")
        echo "🚀 Running GUTAI Go End-to-End Test Suite"
        echo "=========================================="
        ;;
    "all")
        echo "🚀 Running All GUTAI End-to-End Test Suites"
        echo "============================================"
        ;;
    *)
        echo "❌ Unsupported language: $LANGUAGE"
        echo "Usage: $0 [python|go|golang|all]"
        exit 1
        ;;
esac

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run the appropriate E2E test(s)
overall_exit_code=0

if [ "$LANGUAGE" = "python" ] || [ "$LANGUAGE" = "all" ]; then
    echo "🧪 Starting Python E2E test workflow..."
    python3 test_python_e2e.py
    python_exit_code=$?
    if [ $python_exit_code -ne 0 ]; then
        overall_exit_code=1
        echo "❌ Python E2E Test failed!"
    else
        echo "✅ Python E2E Test completed successfully!"
    fi
fi

if [ "$LANGUAGE" = "go" ] || [ "$LANGUAGE" = "golang" ] || [ "$LANGUAGE" = "all" ]; then
    echo "🧪 Starting Go E2E test workflow..."
    python3 test_golang_e2e.py
    go_exit_code=$?
    if [ $go_exit_code -ne 0 ]; then
        overall_exit_code=1
        echo "❌ Go E2E Test failed!"
    else
        echo "✅ Go E2E Test completed successfully!"
    fi
fi

if [ "$LANGUAGE" = "all" ]; then
    if [ $overall_exit_code -eq 0 ]; then
        echo "🎉 All E2E Tests completed successfully!"
    else
        echo "❌ Some E2E Tests failed!"
    fi
fi

exit $overall_exit_code
