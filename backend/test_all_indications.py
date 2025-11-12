#!/usr/bin/env python3
"""
Test script to retrieve ALL indications from ALL labels for a single medication.
Attempts to identify active vs discontinued labels using heuristics.
"""

import urllib.request
import urllib.parse
import json
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Optional


def fetch_all_labels(drug_name: str) -> List[Dict[str, Any]]:
    """Fetch ALL labels for a drug (up to FDA API limit)"""
    base_url = "https://api.fda.gov/drug/label.json"
    
    all_labels = []
    limit = 100
    skip = 0
    max_records = 1000  # Safety cap
    
    print(f"🔍 Fetching all labels for: {drug_name}")
    
    while True:
        params = {
            'search': f'openfda.generic_name:"{drug_name}"',
            'limit': limit,
            'skip': skip
        }
        url = base_url + '?' + urllib.parse.urlencode(params)
        
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status != 200:
                    print(f"  ⚠️  HTTP {response.status} at skip={skip}")
                    break
                
                data = json.load(response)
                results = data.get('results', [])
                
                if not results:
                    break
                
                all_labels.extend(results)
                print(f"  📄 Fetched {len(results)} labels (total: {len(all_labels)})")
                
                # Check if we've hit the end
                meta = data.get('meta', {}).get('results', {})
                total = meta.get('total', 0)
                
                skip += limit
                
                if skip >= total or skip >= max_records:
                    break
                    
        except Exception as e:
            print(f"  ❌ Error at skip={skip}: {e}")
            break
    
    print(f"✅ Total labels fetched: {len(all_labels)}\n")
    return all_labels


def classify_label_status(label: Dict[str, Any], all_labels: List[Dict[str, Any]]) -> str:
    """
    Classify a label as 'active', 'likely_active', 'outdated', or 'unknown'
    
    Heuristics:
    - Active: effective_time within last 2 years AND highest version for its set_id
    - Likely Active: effective_time within last 5 years
    - Outdated: older effective_time or superseded by newer version
    - Unknown: insufficient metadata
    """
    effective_time = label.get('effective_time')
    version = label.get('version')
    set_id = label.get('set_id')
    
    if not effective_time:
        return 'unknown'
    
    # Parse effective_time (YYYYMMDD format)
    try:
        label_date = datetime.strptime(str(effective_time), '%Y%m%d')
    except (ValueError, TypeError):
        return 'unknown'
    
    now = datetime.now()
    age_days = (now - label_date).days
    
    # Check if this is the latest version for its set_id
    if set_id:
        same_set_labels = [l for l in all_labels if l.get('set_id') == set_id]
        if same_set_labels:
            max_version = max(
                (l.get('version', 0) for l in same_set_labels),
                default=0
            )
            is_latest_version = (version == max_version)
        else:
            is_latest_version = True
    else:
        is_latest_version = True
    
    # Classification logic
    if age_days <= 730 and is_latest_version:  # 2 years
        return 'active'
    elif age_days <= 1825:  # 5 years
        return 'likely_active'
    else:
        return 'outdated'


def extract_indications_from_label(label: Dict[str, Any]) -> Optional[str]:
    """Extract indications text from a label"""
    indications = label.get('indications_and_usage')
    
    if isinstance(indications, list) and indications:
        return indications[0]
    elif isinstance(indications, str):
        return indications
    else:
        return None


def analyze_all_indications(drug_name: str):
    """Main analysis function"""
    
    # Fetch all labels
    all_labels = fetch_all_labels(drug_name)
    
    if not all_labels:
        print(f"❌ No labels found for {drug_name}")
        return
    
    # Classify each label
    print("=" * 80)
    print("LABEL CLASSIFICATION")
    print("=" * 80)
    
    status_counts = defaultdict(int)
    labels_by_status = defaultdict(list)
    
    for label in all_labels:
        status = classify_label_status(label, all_labels)
        status_counts[status] += 1
        labels_by_status[status].append(label)
    
    print(f"\n📊 Status Distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status:15s}: {count:3d} labels")
    
    # Group by set_id to identify unique products
    by_set_id = defaultdict(list)
    for label in all_labels:
        set_id = label.get('set_id', 'unknown')
        by_set_id[set_id].append(label)
    
    print(f"\n📦 Unique Products (by set_id): {len(by_set_id)}")
    
    # Show active labels
    print("\n" + "=" * 80)
    print("ACTIVE LABELS (last 2 years, latest version)")
    print("=" * 80)
    
    active_labels = labels_by_status['active']
    
    if not active_labels:
        print("⚠️  No labels classified as 'active'. Showing 'likely_active' instead:")
        active_labels = labels_by_status['likely_active']
    
    for i, label in enumerate(active_labels[:10], 1):  # Show first 10
        openfda = label.get('openfda', {})
        brand_names = openfda.get('brand_name', [])
        manufacturer = openfda.get('manufacturer_name', [None])[0]
        
        print(f"\n{i}. {brand_names[0] if brand_names else 'Generic'}")
        print(f"   Effective Date: {label.get('effective_time')}")
        print(f"   Version: {label.get('version')}")
        print(f"   Manufacturer: {manufacturer}")
        print(f"   Set ID: {label.get('set_id', 'N/A')[:20]}...")
        
        indications = extract_indications_from_label(label)
        if indications:
            preview = indications[:200].replace('\n', ' ')
            print(f"   Indications: {preview}...")
    
    # Extract all unique indications from active labels
    print("\n" + "=" * 80)
    print("ALL UNIQUE INDICATIONS (from active labels)")
    print("=" * 80)
    
    unique_indications = set()
    for label in active_labels:
        indications = extract_indications_from_label(label)
        if indications:
            # Normalize and deduplicate
            normalized = ' '.join(indications.split())
            unique_indications.add(normalized)
    
    print(f"\n📝 Found {len(unique_indications)} unique indication texts\n")
    
    for i, indication_text in enumerate(sorted(unique_indications, key=len, reverse=True)[:5], 1):
        print(f"{i}. ({len(indication_text)} chars)")
        print(f"   {indication_text[:300]}...")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total labels retrieved: {len(all_labels)}")
    print(f"Active labels: {len(labels_by_status['active'])}")
    print(f"Likely active labels: {len(labels_by_status['likely_active'])}")
    print(f"Outdated labels: {len(labels_by_status['outdated'])}")
    print(f"Unknown status: {len(labels_by_status['unknown'])}")
    print(f"Unique indication texts: {len(unique_indications)}")
    
    # Export active labels to JSON
    output_file = f"{drug_name}_active_labels.json"
    export_data = {
        "drug_name": drug_name,
        "analysis_date": datetime.now().isoformat(),
        "total_labels": len(all_labels),
        "active_labels_count": len(active_labels),
        "active_labels": [
            {
                "brand_name": label.get('openfda', {}).get('brand_name', [None])[0],
                "manufacturer": label.get('openfda', {}).get('manufacturer_name', [None])[0],
                "effective_time": label.get('effective_time'),
                "version": label.get('version'),
                "set_id": label.get('set_id'),
                "indications_and_usage": extract_indications_from_label(label),
            }
            for label in active_labels
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Exported active labels to: {output_file}")


if __name__ == "__main__":
    import sys
    
    drug_name = sys.argv[1] if len(sys.argv) > 1 else "aripiprazole"
    
    print(f"\n{'=' * 80}")
    print(f"FDA LABEL ANALYSIS: {drug_name.upper()}")
    print(f"{'=' * 80}\n")
    
    analyze_all_indications(drug_name)

