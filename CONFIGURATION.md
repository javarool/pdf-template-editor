# Configuration Examples

## Claude Desktop Configuration

Add this to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pdf-template-editor": {
      "command": "/absolute/path/to/pdf-template-editor/pdf-editor-server",
      "cwd": "/absolute/path/to/pdf-template-editor",
      "env": {
        "PYTHONPATH": "/absolute/path/to/pdf-template-editor/scripts"
      }
    }
  }
}
```

## Example Alias File

Create a file named `your-template.alias.yaml` next to your PDF:

```yaml
# Template field aliases for your-template.pdf
# Format: coordinate_key: "human_readable_alias"

x72y742_p0_CustomerName: "customer_name"
x72y720_p0_Address: "customer_address" 
x72y698_p0_City: "customer_city"
x72y676_p0_Phone: "customer_phone"
x300y742_p0_InvoiceNumber: "invoice_number"
x300y720_p0_InvoiceDate: "invoice_date"
x300y698_p0_DueDate: "due_date"
x450y600_p0_SubTotal: "subtotal"
x450y580_p0_Tax: "tax_amount"
x450y560_p0_Total: "total_amount"
```

## Usage Examples

### Basic Field Listing
```python
# List all fields in a PDF
fields = list_pdf_fields("/path/to/invoice-template.pdf")
print(fields)
```

### Field Replacement
```python
# Replace multiple fields at once
result = set_pdf_fields("/path/to/invoice-template.pdf", {
    "customer_name": "Acme Corporation",
    "customer_address": "123 Business St",
    "customer_city": "New York, NY 10001",
    "customer_phone": "(555) 123-4567",
    "invoice_number": "INV-2025-001",
    "invoice_date": "January 15, 2025",
    "due_date": "February 14, 2025",
    "subtotal": "$1,350.00",
    "tax_amount": "$108.00", 
    "total_amount": "$1,458.00"
})
```

## Environment Variables

You can set these environment variables for customization:

```bash
# Set default PDF processing options
export PDF_EDITOR_VERBOSE=true
export PDF_EDITOR_COLOR_FILTER=red
export PDF_EDITOR_BACKUP_ENABLED=true
```
