# Excel Export Module - Quick Start Guide

## 30-Second Start

```python
from excel_export import export_solutions_to_excel
from inventory import LotData

# Your solutions from the optimizer
solutions = [
    ([lot1, lot2], [500.0, 1500.0], 1234.56),
    ([lot3, lot4], [800.0, 1200.0], 1150.25)
]

# Your requirements
requirements = {'dc': 80.0, 'fp': 750.0, 'qty': 2000.0}

# Export!
export_solutions_to_excel(solutions, requirements, '/path/to/output.xlsx')
```

Done! You now have a professionally formatted Excel file.

## What You Get

### Excel File Structure

```
📄 output.xlsx
└─ Sheet: "TUTTE_LE_SOLUZIONI"
   ├─ ═══ SOLUZIONE 1 - Score: 1234.56 ═══
   ├─ [Column Headers]
   ├─ [Lot 1 Data]
   ├─ [Lot 2 Data]
   ├─ 📊 Totale: 2000.00 kg | DC: 82.50% | ...
   ├─ [spacing]
   ├─ ═══ SOLUZIONE 2 - Score: 1150.25 ═══
   └─ ...
```

### Formatting
- ✓ Professional styling (colors, borders, fonts)
- ✓ Auto-sized columns
- ✓ Number formatting (percentages, currency)
- ✓ Highlighted estimated data
- ✓ Summary metrics per solution

## Common Use Cases

### 1. Web API (In-Memory Export)

```python
from excel_export import export_solutions_to_bytes

# Generate Excel in memory
excel_bytes = export_solutions_to_bytes(solutions, requirements)

# Send as HTTP response
return Response(
    excel_bytes,
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    headers={'Content-Disposition': 'attachment;filename=blend.xlsx'}
)
```

### 2. Save to Temp File (Current Service Usage)

```python
import tempfile
from excel_export import export_solutions_to_excel

with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
    tmp_path = tmp.name

export_solutions_to_excel(solutions, requirements, tmp_path)

# Read file back
with open(tmp_path, 'rb') as f:
    excel_bytes = f.read()

# Clean up
os.unlink(tmp_path)
```

### 3. Batch Export Multiple Scenarios

```python
scenarios = [
    ('goose_80', solutions_goose_80, req_goose_80),
    ('goose_85', solutions_goose_85, req_goose_85),
    ('duck_90', solutions_duck_90, req_duck_90)
]

for name, sols, reqs in scenarios:
    export_solutions_to_excel(sols, reqs, f'/output/{name}.xlsx')
```

## Data Preparation

### Building Solutions

```python
# Prepare your LotData objects
lot1 = LotData(
    article_code='3|POB',
    lot_code='LOT-001',
    dc_real=85.0,
    fp_real=750.0,
    duck_real=10.0,
    qty_available=1000.0,
    cost_per_kg=100.0,
    # ... other fields
)

lot2 = LotData(...)

# Build solution tuple: (lots, allocations, score)
solution = (
    [lot1, lot2],           # List of LotData objects
    [600.0, 1400.0],        # Kg allocated to each lot
    1234.56                 # Optimization score
)

# Multiple solutions
solutions = [solution1, solution2, solution3]
```

### Requirements Dictionary

```python
requirements = {
    'dc': 80.0,           # Target DC%
    'fp': 750.0,          # Target Fill Power
    'duck': 10.0,         # Target Duck%
    'qty': 2000.0,        # Target quantity (kg)
    'species': 'O'        # Optional: species code
}
```

## Error Handling

```python
from excel_export import export_solutions_to_excel

try:
    export_solutions_to_excel(solutions, requirements, output_path)
    print("✓ Excel exported successfully")

except ValueError as e:
    print(f"Invalid input: {e}")
    # Handle: empty solutions, invalid path, etc.

except IOError as e:
    print(f"File error: {e}")
    # Handle: permission denied, disk full, etc.

except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle: openpyxl errors, data issues, etc.
```

## Troubleshooting

### "Solutions list cannot be empty"
→ Check that you have at least one solution to export

### "Permission denied"
→ Verify the output directory is writable
→ Check file isn't already open in Excel

### "Mismatch between lots and allocations"
→ Ensure each solution has equal length lists
→ Check logs for which solution is problematic

### Excel file looks wrong
→ Verify openpyxl is up to date: `pip install --upgrade openpyxl`
→ Check LotData objects have required attributes

## Testing

### Quick Test

```python
# Run the built-in integration test
python3 integration_test_excel.py
```

### Manual Test

```python
# Create minimal test case
from excel_export import export_solutions_to_excel
from inventory import LotData

lot = LotData(
    article_code='TEST',
    lot_code='TEST-001',
    dc_real=85.0,
    qty_available=1000.0,
    is_estimated=False
)

solutions = [([lot], [1000.0], 100.0)]
requirements = {'dc': 85.0}

export_solutions_to_excel(solutions, requirements, '/tmp/test.xlsx')
print("✓ Check /tmp/test.xlsx")
```

## Performance Tips

1. **Limit solutions**: Export only top N results (e.g., best 10)
2. **Use in-memory**: Faster than file I/O for web APIs
3. **Pre-validate**: Check data before export to fail fast
4. **Batch wisely**: Don't export hundreds of solutions at once

## Next Steps

- **Full docs**: See `README_EXCEL_EXPORT.md` for complete API reference
- **Examples**: Check `integration_test_excel.py` for real usage
- **Implementation**: See `IMPLEMENTATION_SUMMARY.md` for technical details

## Support

If you encounter issues:
1. Check the logs (detailed DEBUG output available)
2. Review error messages (they include context)
3. Run the test suite to verify installation
4. Check the troubleshooting section in README

---

**Quick Links**
- [Full Documentation](README_EXCEL_EXPORT.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [Test Suite](test_excel_export.py)
- [Integration Test](integration_test_excel.py)

**Status**: ✓ Ready for Production
