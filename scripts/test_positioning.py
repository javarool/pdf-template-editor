#!/usr/bin/env python3

import sys
from pathlib import Path
from pdf_template_editor import PDFTemplateEditor

def test_positioning_accuracy():
    """Test positioning accuracy by checking coordinates before and after replacement"""

    project_root = Path(__file__).parent.parent
    pdf_path = project_root / "resources" / "Northland.pdf"

    with PDFTemplateEditor(str(pdf_path)) as editor:
        print("=== BEFORE REPLACEMENT ===")

        # Get original positions
        templates = editor.get_all_templates()
        original_positions = {}

        for page_num in range(len(editor.doc)):
            page = editor.doc[page_num]
            page_dict = page.get_text("dict")

            for block in page_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        span_text = span.get("text", "")
                        span_bbox = span["bbox"]

                        for template in templates:
                            if template in span_text:
                                original_positions[template] = {
                                    'bbox': span_bbox,
                                    'font_size': span.get("size", 12),
                                    'font_name': span.get("font", "unknown"),
                                    'color': span.get("color", 0),
                                    'page': page_num
                                }
                                print(f"Template: {template}")
                                print(f"  Position: {span_bbox}")
                                print(f"  Font: {span.get('font', 'unknown')} @ {span.get('size', 12)}pt")
                                print(f"  Color: {span.get('color', 0)}")
                                print()

        # Apply test replacements
        test_replacements = {template: f"[{template}_REPLACED]" for template in templates}

        print("=== APPLYING REPLACEMENTS ===")
        success = editor.replace_templates(test_replacements)

        if success:
            print("Replacements applied successfully!")
        else:
            print("Failed to apply replacements!")
            return False

        print("\n=== AFTER REPLACEMENT ===")

        # Check new positions
        for page_num in range(len(editor.doc)):
            page = editor.doc[page_num]
            page_dict = page.get_text("dict")

            for block in page_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        span_text = span.get("text", "")
                        span_bbox = span["bbox"]

                        if "_REPLACED]" in span_text:
                            print(f"Replaced text: {span_text}")
                            print(f"  New position: {span_bbox}")
                            print(f"  Font: {span.get('font', 'unknown')} @ {span.get('size', 12)}pt")
                            print(f"  Color: {span.get('color', 0)}")
                            print()

if __name__ == "__main__":
    test_positioning_accuracy()