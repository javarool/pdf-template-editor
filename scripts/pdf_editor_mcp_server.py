#!/usr/bin/env python3
"""
PDF Template Editor MCP Server

A Model Context Protocol server for intelligent PDF template editing.
Provides tools to find and replace template fields in PDF documents.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="importlib._bootstrap")

import os
import sys
import logging
import yaml
from typing import Dict, Optional
from fastmcp import FastMCP
from pdf_template_editor import PDFTemplateEditor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastMCP("PDF Template Editor MCP Server")


def load_alias_mapping(pdf_path: str) -> Dict[str, str]:
    """Load alias mapping from YAML file next to PDF"""
    base_name = os.path.splitext(pdf_path)[0]
    alias_file = f"{base_name}.alias.yaml"

    if not os.path.exists(alias_file):
        return {}

    try:
        with open(alias_file, 'r', encoding='utf-8') as f:
            alias_data = yaml.safe_load(f) or {}
            # Reverse the mapping: coordinate_key -> alias to alias -> coordinate_key
            return {v: k for k, v in alias_data.items()}
    except Exception:
        return {}


def reverse_alias_mapping(alias_map: Dict[str, str]) -> Dict[str, str]:
    """Create reverse mapping from alias to coordinate key"""
    return {v: k for k, v in alias_map.items()}


def validate_pdf_path(pdf_path: str) -> None:
    """Validate PDF file path and accessibility"""
    if not pdf_path or not isinstance(pdf_path, str):
        raise ValueError("pdf_path must be a non-empty string")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError(f"File must be a PDF: {pdf_path}")

    if not os.access(pdf_path, os.R_OK):
        raise PermissionError(f"Cannot read PDF file: {pdf_path}")


@app.tool
def list_pdf_fields(pdf_path: str) -> str:
    """
    List all available fields in PDF with their aliases

    Args:
        pdf_path: Path to the PDF file to analyze

    Returns:
        YAML-formatted string of field aliases and their values

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If path is invalid or file is not a PDF
        PermissionError: If file cannot be read
    """
    try:
        logger.info(f"Listing fields for PDF: {pdf_path}")
        validate_pdf_path(pdf_path)

        # Load alias mapping (returns alias -> coordinate_key)
        alias_to_coord = load_alias_mapping(pdf_path)
        # Create reverse mapping: coordinate_key -> alias
        coord_to_alias = {v: k for k, v in alias_to_coord.items()}

        # Find all fields in PDF with Y sorting to maintain coordinate order
        with PDFTemplateEditor(pdf_path, verbose=False) as editor:
            fields = editor.find_templates(filter_by_color="red", sort_by_y=True)

        if not fields:
            return "No template fields found in the PDF. Make sure template fields are marked in red color."

        # Build ordered result maintaining the coordinate-based order from fields
        result_lines = []
        for field in fields:
            coord_key = field["key"]
            alias = coord_to_alias.get(coord_key, coord_key)
            # Format as YAML key-value pair
            result_lines.append(f"{alias}: \"{field['text']}\"")

        logger.info(f"Found {len(fields)} template fields")
        return '\n'.join(result_lines)

    except (FileNotFoundError, ValueError, PermissionError) as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing PDF file {pdf_path}: {str(e)}")
        raise Exception(f"Error processing PDF file {pdf_path}: {str(e)}")


@app.tool
def set_pdf_fields(pdf_path: str, fields: Dict[str, str]) -> str:
    """
    Set field values in PDF using aliases

    Args:
        pdf_path: Path to PDF file
        fields: Dictionary of alias_name: value pairs

    Returns:
        Success message with number of fields updated

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If path/fields are invalid
        PermissionError: If file cannot be accessed
    """
    try:
        logger.info(f"Setting fields in PDF: {pdf_path}")
        validate_pdf_path(pdf_path)

        if not fields or not isinstance(fields, dict):
            raise ValueError("fields must be a non-empty dictionary")

        if not os.access(pdf_path, os.W_OK):
            raise PermissionError(f"Cannot write to PDF file: {pdf_path}")

        # Load alias mapping (returns alias -> coordinate_key)
        alias_to_coord = load_alias_mapping(pdf_path)

        if not alias_to_coord:
            logger.warning(f"No alias mapping found for {pdf_path}. Using field names as coordinate keys.")

        # Convert alias fields to coordinate-based fields
        coordinate_fields = {}
        for alias, value in fields.items():
            coord_key = alias_to_coord.get(alias, alias)
            coordinate_fields[coord_key] = str(value)

        # Apply replacements using the PDF editor
        with PDFTemplateEditor(pdf_path, verbose=True) as editor:
            success = editor.replace_templates(coordinate_fields)

            if success:
                # Save the modified PDF
                editor.save()
                logger.info(f"Successfully updated {len(fields)} fields")
                return f"✅ Successfully updated {len(fields)} fields in {os.path.basename(pdf_path)}"
            else:
                raise Exception("Failed to replace template fields")

    except (FileNotFoundError, ValueError, PermissionError) as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error setting fields in PDF {pdf_path}: {str(e)}")
        raise Exception(f"Error setting fields in PDF {pdf_path}: {str(e)}")


def main():
    """Main entry point for the MCP server"""
    try:
        logger.info("Starting PDF Template Editor MCP Server...")
        app.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
