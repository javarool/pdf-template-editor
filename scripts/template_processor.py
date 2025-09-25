#!/usr/bin/env python3

import argparse
import yaml
import sys
from pathlib import Path
from pdf_template_editor import PDFTemplateEditor


def generate_mapping(pdf_path: str, output_path: str, filter_color: str = None) -> bool:
    """
    Generate mapping.yaml file with all templates found in PDF

    Args:
        pdf_path: Path to PDF file
        output_path: Path where to save mapping.yaml
        filter_color: Optional color filter ('red')

    Returns:
        True if successful
    """
    try:
        with PDFTemplateEditor(pdf_path) as editor:
            # Use find_templates to get template data with font info and save to file
            # Sort by Y coordinate for better readability
            template_data = editor.find_templates(mapping_file=output_path, filter_by_color=filter_color, sort_by_y=True)

            if not template_data:
                print("No templates found in PDF")
                return False

            # Extract unique text elements for summary
            texts = set()
            for item in template_data:
                texts.add(item["text"])

            print(f"Generated mapping file: {output_path}")
            print(f"Found {len(template_data)} elements ({len(texts)} unique texts):")
            if filter_color:
                print(f"Filtered by color: {filter_color}")

            return True

    except Exception as e:
        print(f"Error generating mapping: {e}")
        return False


def replace_templates(pdf_path: str, mapping_path: str) -> bool:
    """
    Replace templates in PDF using mapping file

    Args:
        pdf_path: Path to PDF file
        mapping_path: Path to mapping.yaml file

    Returns:
        True if successful
    """
    try:
        # Load mapping file
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping = yaml.safe_load(f)

        if not mapping:
            print("Empty mapping file")
            return False

        # Use all mappings, including empty values
        replacements = {k: v for k, v in mapping.items() if v is not None}

        if not replacements:
            print("No replacement values found in mapping file")
            return False

        # Apply replacements
        with PDFTemplateEditor(pdf_path, verbose=False) as editor:
            success = editor.replace_templates(replacements)

            if success:
                print(f"Successfully replaced {len(replacements)} templates:")
                for template, value in replacements.items():
                    print(f"  {template} -> {value}")
            else:
                print("Failed to replace templates")

            return success

    except Exception as e:
        print(f"Error replacing templates: {e}")
        return False


def clear_templates(pdf_path: str) -> bool:
    """
    Remove all remaining templates from PDF

    Args:
        pdf_path: Path to PDF file

    Returns:
        True if successful
    """
    try:
        with PDFTemplateEditor(pdf_path) as editor:
            # First, get all templates before removal
            templates = editor.get_all_templates()

            if not templates:
                print("No templates found to clear")
                return True

            success = editor.remove_templates()

            if success:
                print(f"Successfully removed {len(templates)} template patterns:")
                for template in templates:
                    print(f"  - {template}")
            else:
                print("Failed to remove templates")

            return success

    except Exception as e:
        print(f"Error clearing templates: {e}")
        return False


def main():
    """Main entry point for template processor"""
    parser = argparse.ArgumentParser(description='PDF Template Processor')
    parser.add_argument('pdf_path', help='Path to PDF file')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--generate', metavar='OUTPUT',
                      help='Generate mapping.yaml file')
    group.add_argument('--replace', metavar='MAPPING',
                      help='Replace templates using mapping.yaml file')
    group.add_argument('--clear', action='store_true',
                      help='Remove all templates from PDF')

    parser.add_argument('--filter-color', choices=['red'],
                      help='Filter elements by color (red)')

    args = parser.parse_args()

    # Check if PDF file exists
    if not Path(args.pdf_path).exists():
        print(f"Error: PDF file not found: {args.pdf_path}")
        sys.exit(1)

    success = False

    if args.generate:
        success = generate_mapping(args.pdf_path, args.generate, args.filter_color)
    elif args.replace:
        if not Path(args.replace).exists():
            print(f"Error: Mapping file not found: {args.replace}")
            sys.exit(1)
        success = replace_templates(args.pdf_path, args.replace)
    elif args.clear:
        success = clear_templates(args.pdf_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()