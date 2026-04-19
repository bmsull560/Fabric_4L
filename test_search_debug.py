#!/usr/bin/env python3
"""Debug script for search CLI."""

import os
import tempfile
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from valuefabric.cli.main import app

runner = CliRunner()

# Create temp directory for config
with tempfile.TemporaryDirectory() as tmpdir:
    # Create config file
    config_dir = os.path.join(tmpdir, ".config", "valuefabric")
    os.makedirs(config_dir, exist_ok=True)
    config_file = os.path.join(config_dir, "config.toml")

    with open(config_file, "w") as f:
        f.write("[active_profile]\n")
        f.write('active_profile = "default"\n\n')
        f.write("[profiles]\n")
        f.write("[profiles.default]\n")
        f.write('base_url = "http://test"\n')
        f.write('api_key = "test-key"\n')

    # Patch the config file location
    with patch("valuefabric.cli.config.CONFIG_FILE", config_file):
        with patch("valuefabric.cli.config.CONFIG_DIR", config_dir):
            with patch("valuefabric.cli.search.L3Client") as mock_client_class:
                mock_instance = MagicMock()
                mock_client_class.return_value = mock_instance

                # Create mock response
                mock_response = MagicMock()
                mock_response.query = "test query"
                mock_response.total_results = 0
                mock_response.processing_time_ms = 50
                mock_response.search_type.value = "hybrid"
                mock_response.results = []

                mock_instance.search.return_value = mock_response

                # Run the command
                result = runner.invoke(app, ["search", "test query"])

                print(f"Exit code: {result.exit_code}")
                if result.output:
                    print(f"Output: {result.output[:500]}")
                else:
                    print("Output: None")

                if hasattr(result, "exception") and result.exception:
                    print(f"Exception: {type(result.exception).__name__}: {result.exception}")
