#!/usr/bin/env python3

import asyncio
import os
import sys
import yaml

# Add the scripts directory to the path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from fastmcp import Client
from pdf_editor_mcp_server import app

async def test_mcp_server():
    """Test MCP server using in-memory transport"""

    # Check if we have a test PDF
    test_files = ['/home/vadim/WORK_DIR/McpServers/pdf-template-editor/resources/Northland.pdf']
    test_pdf = None

    for file in test_files:
        if os.path.exists(file):
            test_pdf = file
            break

    if not test_pdf:
        print("No test PDF found. Please create test.pdf to test the server.")
        return

    print(f"Testing with {test_pdf}")

    try:
        # Use in-memory transport (recommended for testing)
        async with Client(app) as client:
            print("✅ Connected to server successfully")

            # Test 1: list_pdf_fields
            print("\n🔍 Testing list_pdf_fields...")
            result = await client.call_tool("list_pdf_fields", {"pdf_path": test_pdf})

            # Parse YAML result
            if result.data:
                try:
                    fields_dict = yaml.safe_load(result.data)
                    print(f"✅ Found {len(fields_dict)} fields in PDF")

                    # Show all fields
                    print("All fields:")
                    for i, (alias, value) in enumerate(fields_dict.items()):
                        print(f"  {i+1}. {alias}: {value}")

                    # Show full YAML output
                    print("\nFull YAML output:")
                    print(result.data)
                except yaml.YAMLError as e:
                    print(f"❌ Error parsing YAML: {e}")
                    print(f"Raw result: {result.data}")
            else:
                print("❌ No data returned")

            # # Test 2: Test with non-existent file (should fail gracefully)
            # print("\n🚫 Testing with non-existent file...")
            # try:
            #     await client.call_tool("list_pdf_fields", {"pdf_path": "/nonexistent/file.pdf"})
            #     print("❌ Expected error but got success")
            # except Exception as e:
            #     print(f"✅ Correctly handled error: {type(e).__name__}")
            #
            # print("\n🎉 All tests completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())