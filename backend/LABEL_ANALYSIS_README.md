# FDA Label Analysis Tool

## Overview

`test_all_indications.py` retrieves **ALL** labels for a medication and classifies them as active, likely active, or outdated.

## Usage

```bash
cd backend
python3 test_all_indications.py <drug_name>

# Examples
python3 test_all_indications.py aripiprazole
python3 test_all_indications.py risperidone
python3 test_all_indications.py haloperidol
```

## How It Works

### 1. Fetches All Labels
- Retrieves up to 1000 labels from FDA API (paginated)
- For aripiprazole: **117 labels**
- For risperidone: **77 labels**

### 2. Classifies Label Status

Since the FDA API doesn't expose `marketing_status` or `discontinuation_date` in the label endpoint, we use **heuristics**:

#### **Active** (recommended for use)
- `effective_time` within last **2 years**
- **Highest version** for its `set_id` (product family)
- Example: 98/117 aripiprazole labels classified as active

#### **Likely Active**
- `effective_time` within last **5 years**
- May not be the latest version
- Example: 14/117 aripiprazole labels

#### **Outdated**
- `effective_time` older than 5 years
- OR superseded by a newer version
- Example: 5/117 aripiprazole labels

### 3. Extracts Unique Indications

- Deduplicates indication texts from active labels
- For aripiprazole: **53 unique indication texts**
- For risperidone: **27 unique indication texts**

### 4. Exports Results

Creates `{drug_name}_active_labels.json` with:
- Brand name
- Manufacturer
- Effective date
- Version
- Set ID
- Full indications text

## Key Findings

### Aripiprazole (117 labels)
- **Active**: 98 labels (84%)
- **Likely Active**: 14 labels (12%)
- **Outdated**: 5 labels (4%)
- **Unique Products**: 117 (by `set_id`)
- **Unique Indications**: 53

### Risperidone (77 labels)
- **Active**: 62 labels (81%)
- **Likely Active**: 13 labels (17%)
- **Outdated**: 2 labels (3%)
- **Unique Indications**: 27

## Identifying Discontinued Labels

### What the FDA API Provides
✅ `effective_time` - date label became effective (YYYYMMDD)
✅ `version` - version number for the label
✅ `set_id` - groups related labels (same product, different versions)
✅ `openfda.brand_name` - brand names
✅ `openfda.manufacturer_name` - manufacturer

### What the FDA API Does NOT Provide
❌ `marketing_status` - not available in label endpoint
❌ `discontinuation_date` - not available
❌ `active` flag - not available

### Alternative: NDC Directory API

For definitive marketing status, cross-reference with the **NDC Directory API**:

```bash
# Check if an NDC is currently marketed
curl "https://api.fda.gov/drug/ndc.json?search=product_ndc:0378-3750"
```

The NDC endpoint includes `marketing_status` field with values:
- `"Prescription"` - actively marketed
- `"Discontinued"` - no longer marketed
- `"None"` - status unknown

### Recommended Approach

1. **Use our heuristic** (effective_time + version) for initial filtering
2. **For critical decisions**, cross-reference NDC codes with NDC Directory API
3. **Focus on labels with `effective_time` within 2 years** - these are almost certainly active

## Sample Output

```
================================================================================
FDA LABEL ANALYSIS: ARIPIPRAZOLE
================================================================================

🔍 Fetching all labels for: aripiprazole
  📄 Fetched 100 labels (total: 100)
  📄 Fetched 17 labels (total: 117)
✅ Total labels fetched: 117

================================================================================
LABEL CLASSIFICATION
================================================================================

📊 Status Distribution:
  active         :  98 labels
  likely_active  :  14 labels
  outdated       :   5 labels

📦 Unique Products (by set_id): 117

================================================================================
ACTIVE LABELS (last 2 years, latest version)
================================================================================

1. Aripiprazole
   Effective Date: 20250203
   Version: 3
   Manufacturer: Preferred Pharmaceuticals Inc.
   Set ID: 02a4af27-c83c-4166-9...
   Indications: 1 INDICATIONS AND USAGE Aripiprazole is indicated for...

[... 97 more active labels ...]

================================================================================
SUMMARY
================================================================================
Total labels retrieved: 117
Active labels: 98
Likely active labels: 14
Outdated labels: 5
Unique indication texts: 53

💾 Exported active labels to: aripiprazole_active_labels.json
```

## Next Steps

To integrate this into the main app:

1. Add a filter toggle: "Show active labels only" (default: ON)
2. Display label age and version in the UI
3. Add a "View all X labels" expandable section
4. Implement NDC cross-reference for definitive status (optional)

