# Quick Fix Reference: CSV Upload ValueError

## Problem
```
ValueError: The truth value of a Series is ambiguous
```

## Location
File: `/app/core/inventory_service.py`
Lines: 300-310, 331, 345, 362, 364

## What Was Changed

### Function Definition (Line 300)
```python
# BEFORE (Buggy)
def get_first_value(row, *column_names):

# AFTER (Fixed)
def get_first_value(*column_names):
```

### Function Calls (4 locations)
```python
# BEFORE (Buggy)
get_first_value(row, 'SCO_DESC')
get_first_value(row, 'SCO_Standard_Nominal')
get_first_value(row, 'SCO_QUALITA')
get_first_value(row, 'SCO_NOTE_LAB', 'SCO_LabNote', ...)

# AFTER (Fixed)
get_first_value('SCO_DESC')
get_first_value('SCO_Standard_Nominal')
get_first_value('SCO_QUALITA')
get_first_value('SCO_NOTE_LAB', 'SCO_LabNote', ...)
```

## Why This Fixes It
- Function now uses **closure** to access `row` from outer loop scope
- Eliminates parameter name shadowing
- Ensures pandas Series always returns scalar values correctly
- No ambiguity in truth value evaluation

## Test Command
```bash
cd /backend
python3 test_csv_fix.py
```

## Verification
```bash
python3 -m py_compile app/core/inventory_service.py
```

## Status
- **Fixed**: Yes
- **Tested**: Yes
- **Breaking Changes**: None
- **Ready for Production**: Yes
