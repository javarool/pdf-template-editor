# PDF Template Editor MCP Server

A Model Context Protocol (MCP) server that provides intelligent PDF template editing capabilities. This server allows you to find template fields in PDF documents and replace them with custom values using coordinate-based positioning and alias mapping.

## 🚀 Features

- **Template Field Detection**: Automatically detect template fields in PDF documents (especially red-colored text)
- **Coordinate-Based Positioning**: Precise field replacement using coordinate mapping
- **Alias System**: Use human-readable field names instead of coordinate keys
- **YAML Configuration**: Easy field mapping configuration
- **MCP Integration**: Seamless integration with MCP-compatible clients (Claude Desktop, etc.)
- **Batch Processing**: Replace multiple fields in a single operation

## 📋 Prerequisites

- Python 3.8 or higher
- Virtual environment support

## 🔧 Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd pdf-template-editor
   ```

2. Run the server (it will automatically set up the virtual environment):
   ```bash
   ./pdf-editor-server
   ```

The script will:
- Create a virtual environment if it doesn't exist
- Install all required dependencies
- Start the MCP server

## 🛠️ Configuration

### MCP Client Setup

Add this server to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "pdf-editor": {
      "command": "/path/to/pdf-template-editor/pdf-editor-server",
      "cwd": "/path/to/pdf-template-editor"
    }
  }
}
```

### Alias Mapping

Create an alias file (`filename.alias.yaml`) next to your PDF file to map coordinate keys to readable names:

```yaml
# example.alias.yaml
x100y200_p0_text: "customer_name"
x150y250_p0_text: "invoice_date"
x200y300_p0_text: "total_amount"
```

## 🎯 Usage

The server provides two main tools:

### 1. List PDF Fields

```
list_pdf_fields(pdf_path: str) -> str
```

Lists all available template fields in a PDF with their aliases.

### 2. Set PDF Fields

```
set_pdf_fields(pdf_path: str, fields: Dict[str, str]) -> str
```

Sets field values in the PDF using alias names.

Example usage:

```python
# List available fields
fields = list_pdf_fields("/path/to/template.pdf")

# Set field values
result = set_pdf_fields("/path/to/template.pdf", {
    "customer_name": "John Doe",
    "invoice_date": "2025-01-15",
    "total_amount": "$1,500.00"
})
```

## 📁 Project Structure

```
pdf-template-editor/
├── pdf-editor-server          # Main executable script
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── scripts/
│   ├── pdf_editor_mcp_server.py    # MCP server implementation
│   ├── pdf_template_editor.py      # Core PDF editing logic
│   ├── template_processor.py       # Template processing utilities
│   └── test_*.py                   # Test files
└── resources/
    ├── example.pdf             # Sample PDF template
    ├── example.alias.yaml      # Sample alias mapping
    └── mapping.yaml            # Additional mappings
```

## 🔍 How It Works

1. **Field Detection**: The system scans PDF documents for text elements, particularly focusing on red-colored text which typically indicates template fields.

2. **Coordinate Mapping**: Each field is identified by its precise coordinates (x, y position) and other attributes.

3. **Alias System**: Coordinate keys are mapped to human-readable aliases via YAML files for easier usage.

4. **Field Replacement**: Text replacement is performed using PyMuPDF with coordinate-based precision.

## 🧪 Testing

Run the test suite:

```bash
cd scripts
python test_mcp.py
python test_positioning.py
```

## 🛡️ Error Handling

The server includes comprehensive error handling for:

- File not found errors
- Invalid PDF files
- Permission issues
- Malformed field mappings
- Network connectivity issues

## 📦 Dependencies

- `PyMuPDF (fitz)`: PDF processing
- `PyYAML`: Configuration file parsing  
- `FastMCP`: MCP protocol implementation
- `typing`: Type hints support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-username/pdf-template-editor/issues) page
2. Create a new issue with detailed information about your problem
3. Include sample PDF files and error messages when possible

## 🚧 Roadmap

- [ ] Support for more field types (checkboxes, images)
- [ ] GUI interface for field mapping
- [ ] Batch processing of multiple PDFs
- [ ] Integration with more MCP clients
- [ ] Docker containerization
- [ ] REST API endpoint option
