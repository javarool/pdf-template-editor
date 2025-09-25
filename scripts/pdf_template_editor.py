#!/usr/bin/env python3

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="importlib._bootstrap")

import fitz
import re
import os
import tempfile
import shutil
import yaml
from typing import List, Dict, Tuple, Optional


class PDFTemplateEditor:
    """PDF Template Editor using PyMuPDF for coordinate-based text replacement"""

    def __init__(self, pdf_path: str, verbose: bool = False):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.verbose = verbose


    def find_templates(self, mapping_file: Optional[str] = None, filter_by_color: str = None, sort_by_y: bool = False) -> List[Dict]:
        """Find all text elements with their font information"""
        results = []

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            page_dict = page.get_text("dict")

            for block in page_dict.get("blocks", []):
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    for span in line.get("spans", []):
                        span_text = span.get("text", "").strip()

                        if span_text:
                            # Check color filter if specified
                            if filter_by_color:
                                color_rgb = self._get_color_rgb(span.get("color", 0))
                                if filter_by_color == "red" and not self._is_red_color(color_rgb):
                                    continue

                            bbox = span.get("bbox", [0, 0, 0, 0])
                            # Use x1, y1, x2, y2 for coordinates
                            x1, y1, x2, y2 = bbox

                            # Create unique key from coordinates and text
                            unique_key = self._serialize_key(x1, y1, x2, y2, span_text, page_num)

                            results.append({
                                "key": unique_key,
                                "text": span_text,
                                "fontFamily": span.get("font", "Unknown"),
                                "size": span.get("size", 12),
                                "bbox": bbox,
                                "page": page_num,
                                "color": self._get_color_rgb(span.get("color", 0)),
                                "matrix": span.get("transform", None)  # Transformation matrix
                            })

        # Sort by page (primary), Y coordinate (secondary) and X coordinate (tertiary) if requested
        if sort_by_y and results:
            results.sort(key=lambda x: (x["page"], round(x["bbox"][1]), x["bbox"][0]))  # page, bbox[1] is Y, bbox[0] is X

        if mapping_file and results:
            self._save_mapping(results, mapping_file)

        return results

    def get_all_templates(self, pattern: str = r'.*') -> List[str]:
        """Get list of unique text elements"""
        templates = set()
        for template_data in self.find_templates(pattern):
            templates.add(template_data["text"])
        return sorted(list(templates))

    def replace_templates(self, replacements: Dict[str, str], text_color: Tuple[float, float, float] = (0, 0, 0)) -> bool:
        """Replace elements using coordinate-based keys"""
        try:
            parsed_replacements = self._parse_replacements(replacements)
            total_replaced = 0

            for page_num in range(len(self.doc)):
                page = self.doc[page_num]

                replacements_data = self._find_elements_by_coordinates(page, parsed_replacements)

                if replacements_data:
                    self._apply_replacements(page, replacements_data, text_color)
                    total_replaced += len(replacements_data)

            if self.verbose:
                print(f"Replaced {total_replaced} elements")

            self._save_pdf()
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error replacing templates: {e}")
            return False

    def remove_templates(self, pattern: str = r'\{\{.*?\}\}') -> bool:
        """Remove all template patterns from PDF"""
        try:
            regex = re.compile(pattern)

            for page_num in range(len(self.doc)):
                page = self.doc[page_num]
                text_dict = page.get_text("dict")

                for block in text_dict["blocks"]:
                    if "lines" not in block:
                        continue

                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"]
                            if regex.search(text):
                                bbox = fitz.Rect(span["bbox"])
                                clean_text = regex.sub("", text).strip()

                                page.add_redact_annot(bbox)
                                if clean_text:
                                    page.insert_text(
                                        bbox.tl, clean_text,
                                        fontsize=span.get("size", 12),
                                        fontname=span.get("font", "helv")
                                    )

                page.apply_redactions()

            self._save_pdf()
            return True
        except Exception as e:
            if self.verbose:
                print(f"Error removing templates: {e}")
            return False

    def _parse_replacements(self, replacements: Dict[str, str]) -> List[Dict]:
        """Parse replacement keys into coordinate data"""
        parsed = []
        for key, new_value in replacements.items():
            try:
                x1, y1, x2, y2, original_text = self._deserialize_key(key)
                unescaped_new_value = self._unescape_yaml_value(new_value)

                parsed.append({
                    'key': key, 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'original_text': original_text, 'new_value': unescaped_new_value
                })
            except ValueError as e:
                if self.verbose:
                    print(f"Skipping invalid key {key}: {e}")
        return parsed

    def _find_elements_by_coordinates(self, page, parsed_replacements: List[Dict]) -> List[Dict]:
        """Find elements by exact coordinate and text match"""
        replacements_data = []
        page_dict = page.get_text("dict")

        for block in page_dict.get("blocks", []):
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line.get("spans", []):
                    span_text = span.get("text", "").strip()
                    bbox = span.get("bbox", [0, 0, 0, 0])

                    # Use x1, y1, x2, y2 for coordinates
                    x1, y1, x2, y2 = bbox

                    # Find matching replacement
                    for repl_data in parsed_replacements:
                        if self._coordinates_match(x1, y1, x2, y2, span_text, repl_data):
                            replacements_data.append({
                                'rect': fitz.Rect(bbox),
                                'replacement': repl_data['new_value'],
                                'font_size': span.get("size", 12),
                                'font_name': span.get("font", "helv"),
                                'color': self._get_color_rgb(span.get("color", 0)),
                                'key': repl_data['key'],
                                'matrix': span.get("transform", None)  # Original transformation matrix
                            })
                            break

        return replacements_data

    def _coordinates_match(self, x1: float, y1: float, x2: float, y2: float, text: str, repl_data: Dict) -> bool:
        """Check if coordinates and text match replacement data"""
        # Allow small tolerance for coordinate differences (±10 pixels tolerance)
        tolerance = 10.0

        expected_x1 = repl_data['x1']
        expected_y1 = repl_data['y1']
        expected_x2 = repl_data['x2']
        expected_y2 = repl_data['y2']

        x1_match = abs(expected_x1 - x1) <= tolerance
        y1_match = abs(expected_y1 - y1) <= tolerance
        x2_match = abs(expected_x2 - x2) <= tolerance
        y2_match = abs(expected_y2 - y2) <= tolerance
        text_match = repl_data['original_text'] == text

        matches = x1_match and y1_match and x2_match and y2_match and text_match

        # if self.verbose and "Oripov7764" in text:
        #     print(f"Debug match for:")
        #     print(f"  Expected: x1={expected_x1:.2f}, y1={expected_y1:.2f}, x2={expected_x2:.2f}, y2={expected_y2:.2f}")
        #     print(f"  Found:    x1={x1:.2f}, y1={y1:.2f}, x2={x2:.2f}, y2={y2:.2f}")
        #     print(f"  Found text:   '{text}' (len={len(text)})")
        #     print(f"  Text match: {text_match}, Coords match: {x1_match and y1_match and x2_match and y2_match}")
        #     print(f"  Overall match: {matches}")

        return matches

    def _apply_replacements(self, page, replacements_data: List[Dict], text_color: Tuple[float, float, float]):
        """Apply replacements to page"""
        if self.verbose:
            print(f"Applying {len(replacements_data)} replacements on page {page.number}")

        # Remove old text precisely
        for data in replacements_data:
            if self.verbose:
                print(f"Removing: {data['key']}")
            self._remove_specific_text(page, data)

        # Insert new text
        for data in replacements_data:
            if self.verbose:
                print(f"Inserting: '{data['replacement']}' at {data['rect']}")
            self._insert_text_with_formatting(page, data, text_color)

    def _remove_specific_text(self, page, data: Dict):
        """Remove specific text element precisely without affecting neighbors"""
        rect = data['rect']

        # Extract original text from key
        key = data['key']
        _, _, _, _, original_text = self._deserialize_key(key)

        if self.verbose:
            print(f"  Removing text: '{original_text}' at {rect}")

        # Search for the exact text in the exact location
        text_instances = page.search_for(original_text)

        if self.verbose:
            print(f"  Found {len(text_instances)} instances of '{original_text}':")
            for i, inst in enumerate(text_instances):
                print(f"    Instance {i}: {inst}")

        # Find the instance that matches our coordinates
        target_rect = None
        for i, instance_rect in enumerate(text_instances):
            # Check if this instance overlaps with our target rect (increased tolerance)
            if (abs(instance_rect.x0 - rect.x0) < 10 and
                abs(instance_rect.y0 - rect.y0) < 10 and
                abs(instance_rect.x1 - rect.x1) < 10 and
                abs(instance_rect.y1 - rect.y1) < 10):
                target_rect = instance_rect
                if self.verbose:
                    print(f"    Match found with instance {i}")
                break

        # If we found the exact match, redact only that area
        if target_rect:
            if self.verbose:
                print(f"  Redacting area: {target_rect}")
            page.add_redact_annot(target_rect)
            # Apply redactions but preserve graphics (path elements like checkboxes)
            page.apply_redactions(graphics=0)  # PDF_REDACT_LINE_ART_NONE = 0
            if self.verbose:
                print(f"  Redaction applied successfully")
        else:
            if self.verbose:
                print(f"  ERROR: No matching text instance found for '{original_text}'")
                print(f"  Target rect: {rect}")
                print(f"  Available instances: {text_instances}")

    def _insert_text_with_formatting(self, page, data: Dict, text_color: Tuple[float, float, float]):
        """Insert text with proper formatting"""
        rect = data['rect']
        font_size = data['font_size']
        font_name = data['font_name']
        text = data['replacement']

        # Use standard baseline positioning
        rect_height = rect.y1 - rect.y0
        position = (rect.x0, rect.y0 + rect_height * 0.8)

        # Use insert_htmlbox for automatic font detection
        try:
            # Convert color to CSS format
            css_color = f"rgb({int(text_color[0]*255)}, {int(text_color[1]*255)}, {int(text_color[2]*255)})"

            # Proper CSS with body selector
            css = f"body {{ margin: 0; padding: 0; font-size: {font_size}px; color: {css_color}; }}"

            page.insert_htmlbox(
                rect,
                text,
                css=css
            )
            if self.verbose:
                print(f"  Inserted text: '{text}' with htmlbox (auto font)")
        except Exception as e:
            if self.verbose:
                print(f"  HTMLBox failed: {e}, trying insert_text")

            # Fallback to insert_text
            try:
                page.insert_text(
                    position,
                    text,
                    fontsize=font_size,
                    fontname='helv',
                    color=text_color
                )
                if self.verbose:
                    print(f"  Fallback: inserted with helv font")
            except Exception as e2:
                if self.verbose:
                    print(f"  All methods failed: {e2}")



    def _get_color_rgb(self, color_int: int) -> Tuple[float, float, float]:
        """Convert color integer to RGB tuple"""
        if isinstance(color_int, int):
            r = (color_int >> 16) & 0xFF
            g = (color_int >> 8) & 0xFF
            b = color_int & 0xFF
            return (r/255.0, g/255.0, b/255.0)
        return (0, 0, 0)

    def _is_red_color(self, color_rgb: Tuple[float, float, float]) -> bool:
        """Check if color is red (R > 0.5 and G,B < 0.3)"""
        r, g, b = color_rgb
        return r > 0.5 and g < 0.3 and b < 0.3

    def _serialize_key(self, x1: float, y1: float, x2: float, y2: float, text: str, page_num: int = 0) -> str:
        """Serialize coordinates and text into key format, rounding floats to 3 decimals"""
        x1 = round(x1, 3)
        y1 = round(y1, 3)
        x2 = round(x2, 3)
        y2 = round(y2, 3)
        escaped_text = self._escape_yaml_value(text)
        return f"p{page_num}_x{x1}y{y1}a{x2}b{y2}_{escaped_text}"

    def _deserialize_key(self, key: str) -> Tuple[float, float, float, float, str]:
        """Deserialize key into coordinates and unescaped text"""
        try:
            # Split by '_' to separate page+coordinates from text
            page_coord_part, escaped_text = key.split('_', 2)[-2:]  # Take last 2 parts

            # Remove page part if it exists
            if '_' in key:
                coord_part = key.split('_')[1] if key.startswith('p') else key.split('_')[0]
            else:
                coord_part = key

            # Parse coordinates: x...y...a...b...
            x1_start = coord_part.find('x') + 1
            y1_start = coord_part.find('y')
            x2_start = coord_part.find('a')
            y2_start = coord_part.find('b')

            x1 = float(coord_part[x1_start:y1_start])
            y1 = float(coord_part[y1_start+1:x2_start])
            x2 = float(coord_part[x2_start+1:y2_start])
            y2 = float(coord_part[y2_start+1:])

            unescaped_text = self._unescape_yaml_value(escaped_text)
            return x1, y1, x2, y2, unescaped_text

        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid key format: {key}") from e

    def _escape_yaml_value(self, text: str) -> str:
        """Escape special characters for YAML"""
        # Order matters: escape backslashes first, then others
        escaped = text.replace('\\', '\\\\')  # Escape backslashes first
        escaped = escaped.replace('\n', '\\n')  # Escape newlines
        escaped = escaped.replace('\r', '\\r')  # Escape carriage returns
        escaped = escaped.replace('\t', '\\t')  # Escape tabs
        escaped = escaped.replace('"', '\\"')  # Escape quotes
        escaped = escaped.replace("'", "\\'")  # Escape single quotes
        return escaped

    def _unescape_yaml_value(self, text: str) -> str:
        """Unescape special characters from YAML"""
        # Order matters: unescape everything else first, then backslashes
        unescaped = text.replace('\\n', '\n')  # Restore newlines
        unescaped = unescaped.replace('\\r', '\r')  # Restore carriage returns
        unescaped = unescaped.replace('\\t', '\t')  # Restore tabs
        unescaped = unescaped.replace('\\"', '"')  # Restore quotes
        unescaped = unescaped.replace("\\'", "'")  # Restore single quotes
        unescaped = unescaped.replace('\\\\', '\\')  # Restore backslashes last
        return unescaped

    def _save_mapping(self, results: List[Dict], mapping_file: str):
        """Save template mapping to YAML file in key:value format"""
        # Create mapping in the order of results (preserves sorting if applied)
        mapping_data = {}
        for item in results:
            escaped_text = self._escape_yaml_value(item["text"])
            mapping_data[item["key"]] = escaped_text

        try:
            with open(mapping_file, 'w', encoding='utf-8') as f:
                # Use default_style='"' to force quoted strings for consistency
                # Use sort_keys=False to preserve insertion order (Python 3.7+)
                yaml.dump(mapping_data, f,
                         default_flow_style=False,
                         allow_unicode=True,
                         default_style='"',
                         width=1000,  # Prevent line wrapping
                         sort_keys=False)  # Preserve insertion order
            if self.verbose:
                print(f"Template mapping saved to: {mapping_file}")
        except Exception as e:
            if self.verbose:
                print(f"Error saving mapping file: {e}")

    def _save_pdf(self):
        """Save PDF to temporary file and replace original"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            temp_path = tmp.name

        # Optimize fonts before saving
        try:
            self.doc.subset_fonts()
            if self.verbose:
                print("  Fonts optimized with subset_fonts()")
        except Exception as e:
            if self.verbose:
                print(f"  Font optimization failed: {e}")

        self.doc.save(temp_path)
        self.doc.close()
        shutil.move(temp_path, self.pdf_path)
        self.doc = fitz.open(self.pdf_path)

    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()