from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import asyncio
import time
import pandas as pd
import io
import os
import json
import re
from pathlib import Path
from functools import lru_cache
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
INDICATION_TREE_PROMPT_PATH = PROMPTS_DIR / "indication_tree_prompt.txt"


@lru_cache(maxsize=1)
def load_indication_tree_prompt() -> str:
    try:
        return INDICATION_TREE_PROMPT_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        print(f"⚠️ [AI PROMPT] Indication tree prompt file not found at {INDICATION_TREE_PROMPT_PATH}")
        return ""


app = FastAPI(
    title="FDA Drug Search API v2",
    description="High-performance FDA drug data search and retrieval",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class DrugResult(BaseModel):
    drug: str
    last_updated: str
    indications_and_usage: str
    indications: Optional[List[str]] = None
    ai_summary: Optional[str] = None
    generic_name: Optional[str] = None
    brand_names: Optional[List[str]] = None
    manufacturer: Optional[str] = None
    approval_date: Optional[str] = None
    route: Optional[List[str]] = None
    dosage_form: Optional[List[str]] = None
    strength: Optional[List[str]] = None
    ndc: Optional[List[str]] = None
    application_number: Optional[str] = None
    product_type: Optional[str] = None

class BatchQueryRequest(BaseModel):
    drugs: List[str]
    include_fields: Optional[List[str]] = None
    rate_limit_delay: Optional[float] = 0.3

class BatchQueryResponse(BaseModel):
    results: List[DrugResult]
    total_processed: int
    total_found: int
    errors: List[Dict[str, str]]
    execution_time: float

class SearchFilters(BaseModel):
    drug_name: Optional[str] = None
    manufacturer: Optional[str] = None
    approval_year_start: Optional[int] = None
    approval_year_end: Optional[int] = None
    product_type: Optional[str] = None
    route: Optional[str] = None
    dosage_form: Optional[str] = None

# FDA API client
class FDAClient:
    BASE_URL = "https://api.fda.gov/drug/label.json"
    
    @staticmethod
    async def search_drug(drug_name: str) -> DrugResult:
        """Search for a single drug - mirrors your original query logic"""
        base_query = f'{FDAClient.BASE_URL}?search=openfda.generic_name:"{drug_name}"'
        limit = 100
        skip = 0
        max_records = 300  # safety cap to avoid excessive paging
        all_entries: List[Dict[str, Any]] = []
        meta_info: Dict[str, Any] = {}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                while True:
                    paged_url = f"{base_query}&limit={limit}&skip={skip}"
                    response = await client.get(paged_url)
                    
                    if response.status_code != 200:
                        return DrugResult(
                            drug=drug_name,
                            last_updated='Error',
                            indications_and_usage=f'HTTP error: {response.status_code}',
                            indications=None
                        )
                    
                    data = response.json()
                    meta_info = data.get('meta', {})
                    entries = data.get('results', []) or []
                    
                    all_entries.extend(entries)
                    
                    results_meta = meta_info.get('results', {})
                    total = results_meta.get('total')
                    
                    if not entries:
                        break
                    
                    skip += limit
                    
                    if total is not None and skip >= total:
                        break
                    
                    if len(all_entries) >= max_records:
                        break
                
                if not all_entries:
                    return DrugResult(
                        drug=drug_name,
                        last_updated='N/A',
                        indications_and_usage='No data found',
                        indications=None
                    )
                
                def entry_score(entry: Dict[str, Any]) -> tuple[int, int]:
                    effective_time = entry.get('effective_time')
                    version = entry.get('version')
                    
                    def to_int(value, default=0):
                        if value is None:
                            return default
                        if isinstance(value, int):
                            return value
                        try:
                            return int(str(value))
                        except (TypeError, ValueError):
                            return default
                    
                    eff_int = to_int(effective_time, 0)
                    ver_int = to_int(version, 0)
                    return (eff_int, ver_int)
                
                best_entry = max(all_entries, key=entry_score)
                
                last_updated = (
                    best_entry.get('effective_time')
                    or meta_info.get('last_updated')
                    or 'N/A'
                )
                
                print(
                    f"\n📄 [LABEL] Selected entry for '{drug_name}': "
                    f"effective_time={best_entry.get('effective_time')}, "
                    f"version={best_entry.get('version')}, "
                    f"total_candidates={len(all_entries)}"
                )
                
                openfda = best_entry.get('openfda', {})

                def get_first(value):
                    if isinstance(value, list):
                        return value[0] if value else None
                    return value

                indications_text = best_entry.get('indications_and_usage', ['Not found'])
                indications_text = (
                    indications_text[0]
                    if isinstance(indications_text, list) and indications_text
                    else (indications_text or 'Not found')
                )
                extracted_indications = extract_indications(indications_text)
                label_metadata = {
                    "effective_time": best_entry.get('effective_time'),
                    "version": best_entry.get('version'),
                    "brand_names": openfda.get('brand_name', []),
                    "manufacturer": get_first(openfda.get('manufacturer_name')),
                    "application_number": get_first(openfda.get('application_number')),
                }
                
                # Generate AI summary (non-blocking, optional)
                ai_summary = None
                try:
                    print(f"\n🔍 [SEARCH] Processing drug: {drug_name}")
                    ai_summary = await generate_ai_summary(drug_name, indications_text, label_metadata)
                except Exception as e:
                    print(f"❌ [SEARCH] AI summary generation failed (non-critical): {e}")
                
                return DrugResult(
                    drug=drug_name,
                    last_updated=last_updated,
                    indications_and_usage=indications_text,
                    indications=extracted_indications if extracted_indications else None,
                    ai_summary=ai_summary,
                    generic_name=get_first(openfda.get('generic_name')),
                    brand_names=openfda.get('brand_name', []),
                    manufacturer=get_first(openfda.get('manufacturer_name')),
                    approval_date=get_first(openfda.get('original_packager_product_ndc')),
                    route=openfda.get('route', []),
                    dosage_form=openfda.get('dosage_form', []),
                    strength=openfda.get('strength', []),
                    ndc=openfda.get('product_ndc', []),
                    application_number=get_first(openfda.get('application_number')),
                    product_type=get_first(openfda.get('product_type'))
                )
                    
            except Exception as e:
                return DrugResult(
                    drug=drug_name,
                    last_updated='Error',
                    indications_and_usage=str(e),
                    indications=None
                )

# Routes
@app.get("/")
async def root():
    return {"message": "FDA Drug Search API v2", "status": "active"}

@app.get("/api/drugs/search/{drug_name}", response_model=DrugResult)
async def search_single_drug(drug_name: str):
    """Search for a single drug by name"""
    result = await FDAClient.search_drug(drug_name)
    return result

@app.get("/api/drugs/search/{drug_name}/stream")
async def search_single_drug_stream(drug_name: str):
    """Search for a single drug with progress updates via SSE"""
    async def event_generator():
        try:
            # Step 1: Searching FDA
            yield f"data: {json.dumps({'step': 'searching', 'message': 'Searching FDA database...', 'status': 'in_progress'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Perform FDA search (simplified inline version)
            base_query = f'{FDAClient.BASE_URL}?search=openfda.generic_name:"{drug_name}"'
            limit = 100
            skip = 0
            max_records = 300
            all_entries = []
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                while True:
                    paged_url = f"{base_query}&limit={limit}&skip={skip}"
                    response = await client.get(paged_url)
                    
                    if response.status_code != 200:
                        yield f"data: {json.dumps({'step': 'error', 'message': f'FDA API error: {response.status_code}', 'status': 'error'})}\n\n"
                        return
                    
                    data = response.json()
                    entries = data.get('results', []) or []
                    all_entries.extend(entries)
                    
                    if not entries or skip >= max_records:
                        break
                    skip += limit
            
            if not all_entries:
                yield f"data: {json.dumps({'step': 'error', 'message': 'No data found', 'status': 'error'})}\n\n"
                return
            
            # Step 2: Selecting best label
            yield f"data: {json.dumps({'step': 'selecting', 'message': f'Selecting best label ({len(all_entries)} found)...', 'status': 'in_progress'})}\n\n"
            await asyncio.sleep(0.1)
            
            def entry_score(entry):
                def to_int(value, default=0):
                    if value is None:
                        return default
                    if isinstance(value, int):
                        return value
                    try:
                        return int(str(value))
                    except (TypeError, ValueError):
                        return default
                eff_int = to_int(entry.get('effective_time'), 0)
                ver_int = to_int(entry.get('version'), 0)
                return (eff_int, ver_int)
            
            best_entry = max(all_entries, key=entry_score)
            
            # Step 3: Generating AI summary
            yield f"data: {json.dumps({'step': 'ai_summary', 'message': 'Generating AI summary...', 'status': 'in_progress'})}\n\n"
            
            # Extract indications
            openfda = best_entry.get('openfda', {})
            indications_text = best_entry.get('indications_and_usage', ['Not found'])
            indications_text = indications_text[0] if isinstance(indications_text, list) and indications_text else (indications_text or 'Not found')
            
            label_metadata = {
                "effective_time": best_entry.get('effective_time'),
                "version": best_entry.get('version'),
                "brand_names": openfda.get('brand_name', []),
                "manufacturer": openfda.get('manufacturer_name', [None])[0],
                "application_number": openfda.get('application_number', [None])[0],
            }
            
            ai_summary = None
            try:
                ai_summary = await generate_ai_summary(drug_name, indications_text, label_metadata)
            except Exception as e:
                print(f"AI summary failed: {e}")
            
            # Step 4: Complete
            yield f"data: {json.dumps({'step': 'complete', 'message': 'Complete', 'status': 'complete'})}\n\n"
            
            # Send final result
            result = DrugResult(
                drug=drug_name,
                last_updated=best_entry.get('effective_time') or 'N/A',
                indications_and_usage=indications_text,
                indications=extract_indications(indications_text) if indications_text else None,
                ai_summary=ai_summary,
                generic_name=openfda.get('generic_name', [None])[0],
                brand_names=openfda.get('brand_name', []),
                manufacturer=openfda.get('manufacturer_name', [None])[0],
                approval_date=openfda.get('original_packager_product_ndc', [None])[0],
                route=openfda.get('route', []),
                dosage_form=openfda.get('dosage_form', []),
                strength=openfda.get('strength', []),
                ndc=openfda.get('product_ndc', []),
                application_number=openfda.get('application_number', [None])[0],
                product_type=openfda.get('product_type', [None])[0]
            )
            
            yield f"data: {json.dumps({'step': 'result', 'result': result.dict()})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'message': str(e), 'status': 'error'})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/indications/search/{indication}/stream")
async def search_by_indication_stream(indication: str, active_only: bool = False):
    """Search FDA labels by indication text with live SSE updates"""
    from collections import defaultdict
    import time
    
    async def event_generator():
        try:
            start_time = time.time()
            
            yield f"data: {json.dumps({'type': 'log', 'message': f'🔍 Searching for: {indication}'})}\n\n"
            await asyncio.sleep(0.05)
            
            # Fetch all labels
            base_query = f'{FDAClient.BASE_URL}?search=indications_and_usage:"{indication}"'
            limit = 100
            skip = 0
            all_labels = []
            total_available = None
            batch_count = 0
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                while True:
                    batch_count += 1
                    
                    yield f"data: {json.dumps({'type': 'log', 'message': f'📦 Fetching batch {batch_count} (skip={skip}, limit={limit})...'})}\n\n"
                    
                    paged_url = f"{base_query}&limit={limit}&skip={skip}"
                    response = await client.get(paged_url)
                    
                    if response.status_code != 200:
                        yield f"data: {json.dumps({'type': 'error', 'message': f'HTTP error {response.status_code}'})}\n\n"
                        return
                    
                    data = response.json()
                    entries = data.get('results', []) or []
                    all_labels.extend(entries)
                    
                    if total_available is None:
                        meta = data.get('meta', {}).get('results', {})
                        total_available = meta.get('total', 0)
                        yield f"data: {json.dumps({'type': 'log', 'message': f'→ FDA reports {total_available} total labels available'})}\n\n"
                        if total_available > 0:
                            estimated_batches = (total_available + limit - 1) // limit
                            yield f"data: {json.dumps({'type': 'log', 'message': f'→ Estimated batches needed: {estimated_batches}'})}\n\n"
                    
                    yield f"data: {json.dumps({'type': 'log', 'message': f'   ✓ Fetched {len(entries)} labels (total: {len(all_labels)})'})}\n\n"
                    
                    if not entries:
                        break
                    
                    skip += limit
                    
                    if total_available and skip >= total_available:
                        yield f"data: {json.dumps({'type': 'log', 'message': f'→ Reached total available ({total_available})'})}\n\n"
                        break
            
            fetch_time = time.time() - start_time
            yield f"data: {json.dumps({'type': 'log', 'message': f'✅ Fetched {len(all_labels)} labels in {fetch_time:.2f}s'})}\n\n"
            
            if not all_labels:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No labels found'})}\n\n"
                return
            
            # Group by drug
            yield f"data: {json.dumps({'type': 'log', 'message': '🔬 Grouping labels by drug...'})}\n\n"
            drugs_map = defaultdict(list)
            for label in all_labels:
                generic_names = label.get('openfda', {}).get('generic_name', [])
                if generic_names:
                    drugs_map[generic_names[0]].append(label)
            
            yield f"data: {json.dumps({'type': 'log', 'message': f'   ✓ Grouped into {len(drugs_map)} unique drugs'})}\n\n"
            
            # Classify
            yield f"data: {json.dumps({'type': 'log', 'message': '🔬 Classifying labels...'})}\n\n"
            
            def classify_status(label: Dict[str, Any], all_drug_labels: List[Dict[str, Any]]) -> str:
                effective_time = label.get('effective_time')
                version = label.get('version')
                set_id = label.get('set_id')
                
                if not effective_time:
                    return 'unknown'
                
                try:
                    label_date = datetime.strptime(str(effective_time), '%Y%m%d')
                except (ValueError, TypeError):
                    return 'unknown'
                
                now = datetime.now()
                age_days = (now - label_date).days
                
                if set_id:
                    same_set = [l for l in all_drug_labels if l.get('set_id') == set_id]
                    max_version = max((l.get('version', 0) for l in same_set), default=0)
                    is_latest = (version == max_version)
                else:
                    is_latest = True
                
                if age_days <= 730 and is_latest:
                    return 'active'
                elif age_days <= 1825:
                    return 'likely_active'
                else:
                    return 'outdated'
            
            def get_latest_date(labels: List[Dict[str, Any]]) -> str:
                dates = [l.get('effective_time', '') for l in labels if l.get('effective_time')]
                return max(dates) if dates else ''
            
            def extract_brand_names(labels: List[Dict[str, Any]]) -> List[str]:
                brands = set()
                for label in labels:
                    brand_list = label.get('openfda', {}).get('brand_name', [])
                    brands.update(brand_list)
                return sorted(list(brands))[:5]
            
            def detect_monotherapy(labels: List[Dict[str, Any]]) -> bool:
                for label in labels:
                    text = label.get('indications_and_usage', '')
                    if isinstance(text, list):
                        text = ' '.join(text)
                    if 'monotherapy' in text.lower():
                        return True
                return False
            
            def detect_adjunctive(labels: List[Dict[str, Any]]) -> bool:
                for label in labels:
                    text = label.get('indications_and_usage', '')
                    if isinstance(text, list):
                        text = ' '.join(text)
                    if 'adjunctive' in text.lower() or 'adjunct' in text.lower():
                        return True
                return False
            
            results = []
            active_drugs = 0
            for drug_name, labels in drugs_map.items():
                status_counts = defaultdict(int)
                for label in labels:
                    status = classify_status(label, labels)
                    status_counts[status] += 1
                
                if active_only and status_counts['active'] == 0:
                    continue
                
                if status_counts['active'] > 0:
                    active_drugs += 1
                
                results.append({
                    'drug_name': drug_name,
                    'total_labels': len(labels),
                    'active_count': status_counts['active'],
                    'likely_active_count': status_counts['likely_active'],
                    'outdated_count': status_counts['outdated'],
                    'latest_date': get_latest_date(labels),
                    'brand_names': extract_brand_names(labels),
                    'has_monotherapy': detect_monotherapy(labels),
                    'has_adjunctive': detect_adjunctive(labels),
                })
            
            yield f"data: {json.dumps({'type': 'log', 'message': f'   ✓ Classified {len(results)} drugs ({active_drugs} active)'})}\n\n"
            
            # Sort
            yield f"data: {json.dumps({'type': 'log', 'message': '📊 Sorting by date...'})}\n\n"
            results.sort(key=lambda x: x['latest_date'], reverse=True)
            
            total_time = time.time() - start_time
            yield f"data: {json.dumps({'type': 'log', 'message': f'✅ Complete! {len(results)} drugs in {total_time:.2f}s'})}\n\n"
            
            # Send final result
            result_data = {
                'indication': indication,
                'total_labels': len(all_labels),
                'total_drugs': len(results),
                'drugs': results
            }
            yield f"data: {json.dumps({'type': 'result', 'data': result_data})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/indications/search/{indication}")
async def search_by_indication(indication: str, active_only: bool = False):
    """Search FDA labels by indication text, group by drug (non-streaming)"""
    from collections import defaultdict
    
    import time
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"🔍 [INDICATION SEARCH] Searching for: '{indication}'")
    print(f"{'='*60}")
    
    # Fetch all labels matching the indication
    base_query = f'{FDAClient.BASE_URL}?search=indications_and_usage:"{indication}"'
    limit = 100
    skip = 0
    all_labels = []
    total_available = None
    batch_count = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            batch_count += 1
            paged_url = f"{base_query}&limit={limit}&skip={skip}"
            
            print(f"  📦 Fetching batch {batch_count} (skip={skip}, limit={limit})...")
            
            response = await client.get(paged_url)
            
            if response.status_code != 200:
                print(f"  ❌ HTTP error {response.status_code}, stopping fetch")
                break
            
            data = response.json()
            entries = data.get('results', []) or []
            all_labels.extend(entries)
            
            # Get total count from first response
            if total_available is None:
                meta = data.get('meta', {}).get('results', {})
                total_available = meta.get('total', 0)
                print(f"  → FDA reports {total_available} total labels available")
                if total_available > 0:
                    estimated_batches = (total_available + limit - 1) // limit
                    print(f"  → Estimated batches needed: {estimated_batches}")
            
            print(f"     ✓ Fetched {len(entries)} labels (total so far: {len(all_labels)})")
            
            # Stop if no more entries or we've fetched everything
            if not entries:
                print(f"  → No more entries returned, stopping")
                break
            
            skip += limit
            
            # Stop if we've fetched all available records
            if total_available and skip >= total_available:
                print(f"  → Reached total available ({total_available}), stopping")
                break
    
    fetch_time = time.time() - start_time
    
    if not all_labels:
        print(f"  ❌ No labels found for indication: {indication}")
        raise HTTPException(status_code=404, detail=f"No labels found for indication: {indication}")
    
    print(f"\n  ✅ Fetched {len(all_labels)} labels in {fetch_time:.2f}s ({len(all_labels)/fetch_time:.1f} labels/sec)")
    
    # Group by generic_name
    print(f"\n  🔬 Grouping labels by generic drug name...")
    drugs_map = defaultdict(list)
    for label in all_labels:
        generic_names = label.get('openfda', {}).get('generic_name', [])
        if generic_names:
            drug_name = generic_names[0]
            drugs_map[drug_name].append(label)
    
    print(f"     ✓ Grouped into {len(drugs_map)} unique drugs")
    
    # Classify and summarize each drug
    def classify_status(label: Dict[str, Any], all_drug_labels: List[Dict[str, Any]]) -> str:
        effective_time = label.get('effective_time')
        version = label.get('version')
        set_id = label.get('set_id')
        
        if not effective_time:
            return 'unknown'
        
        try:
            label_date = datetime.strptime(str(effective_time), '%Y%m%d')
        except (ValueError, TypeError):
            return 'unknown'
        
        now = datetime.now()
        age_days = (now - label_date).days
        
        # Check if latest version for set_id
        if set_id:
            same_set = [l for l in all_drug_labels if l.get('set_id') == set_id]
            max_version = max((l.get('version', 0) for l in same_set), default=0)
            is_latest = (version == max_version)
        else:
            is_latest = True
        
        if age_days <= 730 and is_latest:
            return 'active'
        elif age_days <= 1825:
            return 'likely_active'
        else:
            return 'outdated'
    
    def get_latest_date(labels: List[Dict[str, Any]]) -> str:
        dates = [l.get('effective_time', '') for l in labels if l.get('effective_time')]
        return max(dates) if dates else ''
    
    def extract_brand_names(labels: List[Dict[str, Any]]) -> List[str]:
        brands = set()
        for label in labels:
            brand_list = label.get('openfda', {}).get('brand_name', [])
            brands.update(brand_list)
        return sorted(list(brands))[:5]
    
    def detect_monotherapy(labels: List[Dict[str, Any]]) -> bool:
        for label in labels:
            text = label.get('indications_and_usage', '')
            if isinstance(text, list):
                text = ' '.join(text)
            if 'monotherapy' in text.lower():
                return True
        return False
    
    def detect_adjunctive(labels: List[Dict[str, Any]]) -> bool:
        for label in labels:
            text = label.get('indications_and_usage', '')
            if isinstance(text, list):
                text = ' '.join(text)
            if 'adjunctive' in text.lower() or 'adjunct' in text.lower():
                return True
        return False
    
    print(f"\n  🔬 Classifying labels (active/likely_active/outdated)...")
    results = []
    active_drugs = 0
    for drug_name, labels in drugs_map.items():
        # Classify all labels for this drug
        status_counts = defaultdict(int)
        for label in labels:
            status = classify_status(label, labels)
            status_counts[status] += 1
        
        # Skip if active_only filter is on and no active labels
        if active_only and status_counts['active'] == 0:
            continue
        
        if status_counts['active'] > 0:
            active_drugs += 1
        
        results.append({
            'drug_name': drug_name,
            'total_labels': len(labels),
            'active_count': status_counts['active'],
            'likely_active_count': status_counts['likely_active'],
            'outdated_count': status_counts['outdated'],
            'latest_date': get_latest_date(labels),
            'brand_names': extract_brand_names(labels),
            'has_monotherapy': detect_monotherapy(labels),
            'has_adjunctive': detect_adjunctive(labels),
        })
    
    print(f"     ✓ Classified {len(results)} drugs ({active_drugs} with active labels)")
    
    # Sort by latest_date descending
    print(f"\n  🔬 Detecting treatment modalities (monotherapy/adjunctive)...")
    print(f"     ✓ Detection complete")
    
    print(f"\n  📊 Sorting by latest effective date...")
    results.sort(key=lambda x: x['latest_date'], reverse=True)
    print(f"     ✓ Sorted")
    
    total_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"✅ [INDICATION SEARCH] Complete!")
    print(f"{'='*60}")
    print(f"  Indication: '{indication}'")
    print(f"  Total labels: {len(all_labels)}")
    print(f"  Unique drugs: {len(results)}")
    print(f"  Active drugs: {active_drugs}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"{'='*60}\n")
    
    return {
        'indication': indication,
        'total_labels': len(all_labels),
        'total_drugs': len(results),
        'drugs': results
    }

@app.get("/api/drugs/analyze-labels/{drug_name}")
async def analyze_all_labels(drug_name: str):
    """Analyze all FDA labels for a drug - status distribution, timeline, unique indications"""
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # Fetch all labels
    base_query = f'{FDAClient.BASE_URL}?search=openfda.generic_name:"{drug_name}"'
    limit = 100
    skip = 0
    max_records = 1000
    all_labels = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            paged_url = f"{base_query}&limit={limit}&skip={skip}"
            response = await client.get(paged_url)
            
            if response.status_code != 200:
                break
            
            data = response.json()
            entries = data.get('results', []) or []
            all_labels.extend(entries)
            
            if not entries or skip >= max_records:
                break
            skip += limit
    
    if not all_labels:
        raise HTTPException(status_code=404, detail=f"No labels found for {drug_name}")
    
    # Classify each label
    def classify_status(label: Dict[str, Any]) -> str:
        effective_time = label.get('effective_time')
        version = label.get('version')
        set_id = label.get('set_id')
        
        if not effective_time:
            return 'unknown'
        
        try:
            label_date = datetime.strptime(str(effective_time), '%Y%m%d')
        except (ValueError, TypeError):
            return 'unknown'
        
        now = datetime.now()
        age_days = (now - label_date).days
        
        # Check if latest version for set_id
        if set_id:
            same_set = [l for l in all_labels if l.get('set_id') == set_id]
            max_version = max((l.get('version', 0) for l in same_set), default=0)
            is_latest = (version == max_version)
        else:
            is_latest = True
        
        if age_days <= 730 and is_latest:
            return 'active'
        elif age_days <= 1825:
            return 'likely_active'
        else:
            return 'outdated'
    
    # Process labels
    status_counts = defaultdict(int)
    processed_labels = []
    unique_indications_map = {}  # Map indication text to latest effective_time
    
    for label in all_labels:
        status = classify_status(label)
        status_counts[status] += 1
        
        openfda = label.get('openfda', {})
        indications = label.get('indications_and_usage')
        if isinstance(indications, list) and indications:
            indications_text = indications[0]
        elif isinstance(indications, str):
            indications_text = indications
        else:
            indications_text = ""
        
        # Collect unique indications from active labels with their latest effective_time
        if status == 'active' and indications_text:
            normalized = ' '.join(indications_text.split())
            effective_time = label.get('effective_time', '')
            
            # Keep the latest effective_time for this indication
            if normalized not in unique_indications_map or effective_time > unique_indications_map[normalized]:
                unique_indications_map[normalized] = effective_time
        
        processed_labels.append({
            'effective_time': label.get('effective_time', ''),
            'version': label.get('version', 0),
            'set_id': label.get('set_id', ''),
            'brand_name': openfda.get('brand_name', [None])[0] or 'Generic',
            'manufacturer': openfda.get('manufacturer_name', [None])[0] or 'Unknown',
            'status': status,
            'indications_text': indications_text
        })
    
    # Convert map to list of dicts with text and date
    unique_indications_with_dates = [
        {'text': text, 'latest_date': date}
        for text, date in unique_indications_map.items()
    ]
    # Sort by text length (descending)
    unique_indications_with_dates.sort(key=lambda x: len(x['text']), reverse=True)
    
    return {
        'drug_name': drug_name,
        'total_labels': len(all_labels),
        'active_count': status_counts['active'],
        'likely_active_count': status_counts['likely_active'],
        'outdated_count': status_counts['outdated'],
        'unknown_count': status_counts['unknown'],
        'unique_indications': unique_indications_with_dates,
        'labels': processed_labels
    }

@app.post("/api/drugs/batch", response_model=BatchQueryResponse)
async def batch_query_drugs(request: BatchQueryRequest):
    """
    Batch query multiple drugs - exactly like your antipsychotic script!
    This is the core functionality that replicates your existing code.
    """
    start_time = time.time()
    results = []
    errors = []
    
    print(f"Starting FDA batch query for {len(request.drugs)} drugs...")
    
    for index, drug in enumerate(request.drugs):
        print(f"[{index+1}/{len(request.drugs)}] Querying: {drug}")
        
        try:
            result = await FDAClient.search_drug(drug)
            results.append(result)
            
            if result.indications_and_usage not in ['Not found', 'No data found']:
                print(f"  → Found: {drug} | Last Updated: {result.last_updated}")
            else:
                print(f"  → No results found for {drug}")
                
        except Exception as e:
            error_msg = str(e)
            errors.append({"drug": drug, "error": error_msg})
            print(f"  → Exception for {drug}: {e}")
            
        # Respect API rate limits
        if index < len(request.drugs) - 1:
            await asyncio.sleep(request.rate_limit_delay)
    
    execution_time = time.time() - start_time
    total_found = len([r for r in results if r.indications_and_usage not in ['Not found', 'No data found']])
    
    print(f"\\nBatch query complete. Processed: {len(results)}, Found: {total_found}, Errors: {len(errors)}")
    
    return BatchQueryResponse(
        results=results,
        total_processed=len(results),
        total_found=total_found,
        errors=errors,
        execution_time=execution_time
    )

@app.get("/api/drugs/lists")
async def get_predefined_drug_lists():
    """Get predefined drug lists (like your antipsychotics list)"""
    return {
        "antipsychotics": [
            "chlorpromazine", "fluphenazine", "haloperidol", "loxapine", "molindone",
            "perphenazine", "thioridazine", "thiothixene", "trifluoperazine", "pimozide",
            "clozapine", "risperidone", "olanzapine", "quetiapine", "ziprasidone",
            "aripiprazole", "paliperidone", "amisulpride", "sertindole", "zotepine",
            "lurasidone", "asenapine", "iloperidone", "cariprazine", "brexpiprazole",
            "lumateperone", "aripiprazole lauroxil"
        ],
        "antidepressants": [
            "fluoxetine", "sertraline", "paroxetine", "citalopram", "escitalopram",
            "venlafaxine", "duloxetine", "bupropion", "mirtazapine", "trazodone"
        ],
        "mood_stabilizers": [
            "lithium", "valproate", "carbamazepine", "lamotrigine", "oxcarbazepine"
        ]
    }

@app.post("/api/export/csv")
async def export_to_csv(data: Dict[str, Any]):
    """Export results to CSV - just like your script saves to CSV"""
    results = data.get('results', [])
    filename = data.get('filename', f'FDA_Drug_Results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    
    if not results:
        raise HTTPException(status_code=400, detail="No results to export")
    
    # Convert to DataFrame (like your script)
    df_data = []
    for result in results:
        df_data.append({
            "Drug": result.get('drug'),
            "Last_Updated": result.get('last_updated'),
            "Indications_and_Usage": result.get('indications_and_usage'),
            "Indications": ' | '.join(result.get('indications', [])) if result.get('indications') else '',
            "Generic_Name": result.get('generic_name'),
            "Brand_Names": ', '.join(result.get('brand_names', [])) if result.get('brand_names') else '',
            "Manufacturer": result.get('manufacturer'),
            "Route": ', '.join(result.get('route', [])) if result.get('route') else '',
            "Dosage_Form": ', '.join(result.get('dosage_form', [])) if result.get('dosage_form') else ''
        })
    
    df = pd.DataFrame(df_data)
    
    # Create CSV string
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    
    return StreamingResponse(
        io.BytesIO(csv_content.encode('utf-8')),
        media_type='text/csv',
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ---------------------------
# Helpers
# ---------------------------

async def generate_ai_summary(
    drug_name: str, indications_text: str, label_metadata: Dict[str, Any]
) -> Optional[str]:
    """Generate a structured summary (plus ASCII tree) of the label indications using the shared prompt."""
    print(f"\n🤖 [AI SUMMARY] Generating summary for: {drug_name}")

    prompt_template = load_indication_tree_prompt()
    structured_mode = bool(prompt_template)

    payload = {
        "drug_name": drug_name,
        "indications_and_usage": indications_text,
        "label_metadata": {
            "effective_time": label_metadata.get("effective_time"),
            "version": label_metadata.get("version"),
            "brand_names": label_metadata.get("brand_names", []),
            "manufacturer": label_metadata.get("manufacturer"),
            "application_number": label_metadata.get("application_number"),
        },
    }
    input_json = json.dumps(payload, ensure_ascii=False)

    def parse_structured_output(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        text = text.strip()
        
        # Strip markdown code fences if present
        if text.startswith("```json"):
            text = re.sub(r"^```json\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()
        elif text.startswith("```"):
            text = re.sub(r"^```\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            # Try without json tag
            match = re.search(r"```\s*(\{[\s\S]*?\})\s*```", text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
        return None

    def build_combined_text(structured: Dict[str, Any]) -> Optional[str]:
        if not structured:
            return None
        summary = (structured.get("summary") or "").strip()
        ascii_tree = (structured.get("ascii_tree") or "").strip()
        if summary and ascii_tree:
            return f"{summary}\n\n{ascii_tree}"
        return summary or ascii_tree or None

    def fallback_summary(text: str) -> Optional[str]:
        text = (text or "").strip()
        return text if text else None

    # Try OpenAI first
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            print("  → Trying OpenAI...")
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            model = os.getenv("AI_MODEL", "gpt-4o-mini")
            messages = (
                [
                    {"role": "system", "content": prompt_template},
                    {"role": "user", "content": input_json},
                ]
                if structured_mode
                else [
                    {
                        "role": "system",
                        "content": "You are a medical information specialist. Provide concise, clear summaries.",
                    },
                    {
                        "role": "user",
                        "content": f"Provide a brief 2-3 sentence summary of the key indications for {drug_name}:\n\n{indications_text[:1000]}",
                    },
                ]
            )

            print(
                f"  📤 Payload: model={model}, structured={structured_mode}, input_length={len(input_json)} chars"
            )

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=800,
                response_format={"type": "json_object"} if structured_mode else None,
            )

            content = response.choices[0].message.content.strip()
            structured = parse_structured_output(content) if structured_mode else None
            combined = build_combined_text(structured) if structured else fallback_summary(content)
            if combined:
                print(f"  ✅ OpenAI Success: {len(combined)} chars")
                print(f"  📥 Response: {combined[:120]}...")
                return combined
            else:
                print("  ⚠️ OpenAI returned empty content")
        except Exception as e:
            print(f"  ❌ OpenAI Error: {e}")

    # Try DeepSeek
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        try:
            print("  → Trying DeepSeek...")
            model = os.getenv("AI_MODEL", "deepseek-chat")
            messages = (
                [
                    {"role": "system", "content": prompt_template},
                    {"role": "user", "content": input_json},
                ]
                if structured_mode
                else [
                    {
                        "role": "system",
                        "content": "You are a medical information specialist. Provide concise, clear summaries.",
                    },
                    {
                        "role": "user",
                        "content": f"Provide a brief 2-3 sentence summary of the key indications for {drug_name}:\n\n{indications_text[:1000]}",
                    },
                ]
            )

            print(
                f"  📤 Payload: model={model}, structured={structured_mode}, input_length={len(input_json)} chars"
            )

            async with httpx.AsyncClient(timeout=30.0) as client_http:
                response = await client_http.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {deepseek_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 800,
                        **({"response_format": {"type": "json_object"}} if structured_mode else {}),
                    },
                )

                print(f"  📥 HTTP Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    structured = parse_structured_output(content) if structured_mode else None
                    combined = build_combined_text(structured) if structured else fallback_summary(content)
                    if combined:
                        print(f"  ✅ DeepSeek Success: {len(combined)} chars")
                        print(f"  📥 Response: {combined[:120]}...")
                        return combined
                    else:
                        print("  ⚠️ DeepSeek returned empty content")
                else:
                    print(f"  ❌ DeepSeek HTTP Error: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"  ❌ DeepSeek Error: {e}")

    # Try Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            print("  → Trying Gemini...")
            import google.generativeai as genai
            import asyncio

            genai.configure(api_key=gemini_key)
            model_name = os.getenv("AI_MODEL") or "gemini-flash-latest"
            model = genai.GenerativeModel(model_name)

            print(
                f"  📤 Payload: model={model_name}, structured={structured_mode}, input_length={len(input_json)} chars"
            )

            def generate_sync():
                response = model.generate_content(
                    [prompt_template, input_json] if structured_mode else [f"{drug_name}\n{indications_text[:1000]}"],
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=2048,  # Increased for structured JSON + ASCII tree
                    ),
                )
                # Check finish_reason for debugging
                candidates = getattr(response, "candidates", None) or []
                for candidate in candidates:
                    finish_reason = getattr(candidate, "finish_reason", None)
                    if finish_reason:
                        # finish_reason can be an enum or int (2 = MAX_TOKENS)
                        finish_reason_str = str(finish_reason)
                        if "MAX_TOKENS" in finish_reason_str or finish_reason_str == "2":
                            print(f"  ⚠️  Gemini hit MAX_TOKENS limit, extracting partial content")
                        elif "STOP" not in finish_reason_str and finish_reason_str != "1":
                            print(f"  ⚠️  Gemini finish_reason: {finish_reason_str}")
                
                # Try extracting text manually to avoid `response.text` errors.
                if hasattr(response, "text") and response.text:
                    return response.text
                for candidate in candidates:
                    parts = getattr(candidate, "content", None)
                    if parts and getattr(parts, "parts", None):
                        texts = [
                            getattr(part, "text", "")
                            for part in parts.parts
                            if getattr(part, "text", "")
                        ]
                        if texts:
                            return "\n".join(texts)
                return ""

            content = await asyncio.to_thread(generate_sync)
            content = content.strip()
            structured = parse_structured_output(content) if structured_mode else None
            combined = build_combined_text(structured) if structured else fallback_summary(content)
            if combined:
                print(f"  ✅ Gemini Success: {len(combined)} chars")
                print(f"  📥 Response: {combined[:120]}...")
                return combined
            else:
                print("  ⚠️ Gemini returned empty content")
        except ImportError:
            print("  ⚠️ Gemini library not installed. Run: pip install google-generativeai")
        except Exception as e:
            print(f"  ❌ Gemini Error: {e}")

    print("  ⚠️  No AI provider available or all failed")
    return None

def extract_indications(indications_text: str) -> List[str]:
    """Derive concise indication phrases from the raw INDICATIONS AND USAGE text.

    Heuristics:
    - Prefer sentences/clauses containing keywords like 'indicated', 'treatment of', 'prevention of', 'management of'.
    - Remove leading section numbering like '1 INDICATIONS AND USAGE'.
    - Split into candidate sentences and filter/clean.
    """
    if not indications_text or indications_text.lower() in {"not found", "no data found"}:
        return []

    import re

    # Normalize whitespace and remove section header noise
    text = indications_text
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^\d+\s+(indications?\s+and\s+usage)[:\s-]*", "", text, flags=re.I)

    # Split into sentences conservatively
    candidates = re.split(r"(?<=[.;])\s+", text)

    keywords = [
        r"indicated\s+(?:for|as)",
        r"treatment\s+of",
        r"prevention\s+of",
        r"management\s+of",
        r"adjunctive\s+therapy",
        r"maintenance\s+treatment",
    ]
    keyword_re = re.compile("|".join(keywords), flags=re.I)

    cleaned: List[str] = []
    for sent in candidates:
        s = sent.strip().strip("-•·")
        if len(s) < 20:
            continue
        if keyword_re.search(s):
            cleaned.append(s)

    # Fallback: take up to first 2 substantial sentences if no keyword hits
    if not cleaned:
        for sent in candidates:
            s = sent.strip()
            if len(s) >= 40:
                cleaned.append(s)
            if len(cleaned) >= 2:
                break

    # De-duplicate while preserving order, limit length
    seen = set()
    unique: List[str] = []
    for s in cleaned:
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        # Truncate overly long sentences for readability
        if len(s) > 280:
            s = s[:277].rstrip() + "..."
        unique.append(s)
        if len(unique) >= 6:
            break

    return unique