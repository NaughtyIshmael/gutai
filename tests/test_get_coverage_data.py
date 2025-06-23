#!/usr/bin/env python3
"""
Unit tests for get_coverage_data.py
"""

import unittest
from unittest.mock import Mock, patch
import json
import sys
import os

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from scripts.get_coverage_data import CodecovClient


class TestCodecovClient(unittest.TestCase):
    """Test cases for CodecovClient"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = CodecovClient(
            github_org="bergwolf", github_repo="nydus", codecov_token="test_token"
        )

    @patch("requests.get")
    def test_get_file_coverage_with_hierarchical_data(self, mock_get):
        """Test get_file_coverage with hierarchical tree structure"""
        # Mock the response with the example data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "name": "src",
                "full_path": "src",
                "coverage": 18.704891740176425,
                "lines": 4988,
                "hits": 933,
                "partials": 48,
                "misses": 4007,
                "children": [
                    {
                        "name": "lib.rs",
                        "full_path": "src/lib.rs",
                        "coverage": 52.5,
                        "lines": 40,
                        "hits": 21,
                        "partials": 0,
                        "misses": 19,
                    },
                    {
                        "name": "logger.rs",
                        "full_path": "src/logger.rs",
                        "coverage": 51.82481751824818,
                        "lines": 137,
                        "hits": 71,
                        "partials": 12,
                        "misses": 54,
                    },
                    {
                        "name": "signal.rs",
                        "full_path": "src/signal.rs",
                        "coverage": 0,
                        "lines": 12,
                        "hits": 0,
                        "partials": 0,
                        "misses": 12,
                    },
                    {
                        "name": "bin",
                        "full_path": "src/bin",
                        "coverage": 17.52448426755574,
                        "lines": 4799,
                        "hits": 841,
                        "partials": 36,
                        "misses": 3922,
                    },
                ],
            },
            {
                "name": "api",
                "full_path": "api",
                "coverage": 61.2141652613828,
                "lines": 1779,
                "hits": 1089,
                "partials": 76,
                "misses": 614,
                "children": [
                    {
                        "name": "src",
                        "full_path": "api/src",
                        "coverage": 61.2141652613828,
                        "lines": 1779,
                        "hits": 1089,
                        "partials": 76,
                        "misses": 614,
                    }
                ],
            },
            {
                "name": "utils",
                "full_path": "utils",
                "coverage": 76.68147208121827,
                "lines": 3152,
                "hits": 2417,
                "partials": 67,
                "misses": 668,
                "children": [
                    {
                        "name": "src",
                        "full_path": "utils/src",
                        "coverage": 76.68147208121827,
                        "lines": 3152,
                        "hits": 2417,
                        "partials": 67,
                        "misses": 668,
                    }
                ],
            },
        ]
        mock_get.return_value = mock_response

        # Call the method
        result = self.client.get_file_coverage("main")

        # Verify the request was made correctly
        expected_url = "https://api.codecov.io/api/v2/github/bergwolf/repos/nydus/report/tree?depth=8"
        expected_headers = {
            "accept": "application/json",
            "authorization": "Bearer test_token",
        }
        mock_get.assert_called_once_with(expected_url, headers=expected_headers)

        # Verify the parsed results
        self.assertIsInstance(result, list)

        # Print actual results for debugging
        print("Actual results:", result)

        # Should extract only leaf nodes that are actual files
        expected_files = [
            {"filename": "src/lib.rs", "coverage": 52.5},
            {"filename": "src/logger.rs", "coverage": 51.82481751824818},
        ]

        # Check that all expected files are present
        for expected_file in expected_files:
            self.assertIn(expected_file, result)

        # Check that we don't have directories included
        directory_paths = ["src", "api", "utils", "src/bin", "api/src", "utils/src"]
        for path in directory_paths:
            self.assertNotIn(path, [f["filename"] for f in result])

    @patch("requests.get")
    def test_get_file_coverage_with_results_wrapper(self, mock_get):
        """Test get_file_coverage with data wrapped in results object"""
        # Mock the response with results wrapper
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "name": "test.py",
                    "full_path": "test.py",
                    "coverage": 85.5,
                    "lines": 100,
                    "hits": 85,
                    "partials": 5,
                    "misses": 10,
                }
            ]
        }
        mock_get.return_value = mock_response

        # Call the method
        result = self.client.get_file_coverage("main")

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["filename"], "test.py")
        self.assertEqual(result[0]["coverage"], 85.5)

    @patch("requests.get")
    def test_get_file_coverage_api_error(self, mock_get):
        """Test get_file_coverage with API error response"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the method
        result = self.client.get_file_coverage("main")

        # Verify empty result on error
        self.assertEqual(result, [])

    @patch("requests.get")
    def test_get_file_coverage_invalid_json(self, mock_get):
        """Test get_file_coverage with invalid JSON response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        # Call the method
        result = self.client.get_file_coverage("main")

        # Verify empty result on JSON error
        self.assertEqual(result, [])

    @patch("requests.get")
    def test_get_file_coverage_no_token(self, mock_get):
        """Test get_file_coverage without authentication token"""
        # Create client without token
        client = CodecovClient("bergwolf", "nydus", None)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        # Call the method
        result = client.get_file_coverage("main")

        # Verify request was made without authorization header
        expected_headers = {"accept": "application/json"}
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["headers"], expected_headers)


if __name__ == "__main__":
    unittest.main()
