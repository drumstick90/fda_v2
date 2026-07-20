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
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
INDICATION_TREE_PROMPT_PATH = PROMPTS_DIR / "indication_tree_prompt.txt"


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

class IndicationHistoryRequest(BaseModel):
    drug_name: str
    labels: List[Dict[str, Any]]
    api_key: Optional[str] = None

class DrugSuggestion(BaseModel):
    name: str
    kind: str
    matched_field: str
    label_count: int

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
    RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
    MAX_ATTEMPTS = 3

    @staticmethod
    def _quote_search_value(value: str) -> str:
        escaped = str(value).strip().replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    @staticmethod
    def exact_match_query(field: str, value: str) -> str:
        return f"{field}:{FDAClient._quote_search_value(value)}"

    @staticmethod
    def drug_search_queries(drug_name: str) -> List[Dict[str, str]]:
        return [
            {
                "label": "generic name",
                "query": FDAClient.exact_match_query("openfda.generic_name", drug_name),
            },
            {
                "label": "brand name",
                "query": FDAClient.exact_match_query("openfda.brand_name", drug_name),
            },
            {
                "label": "substance name",
                "query": FDAClient.exact_match_query("openfda.substance_name", drug_name),
            },
        ]

    @staticmethod
    def request_params(search_query: str, limit: int, skip: int) -> Dict[str, Any]:
        return {"search": search_query, "limit": limit, "skip": skip}

    @staticmethod
    def autocomplete_query(field: str, value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9\s-]", " ", value or "")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return ""
        if " " in cleaned:
            return FDAClient.exact_match_query(field, cleaned)
        return f"{field}:{cleaned.lower()}*"

    @staticmethod
    def _suggestion_key(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.lower())

    @staticmethod
    async def suggest_drugs(query: str, limit: int = 10) -> List[DrugSuggestion]:
        cleaned_query = re.sub(r"\s+", " ", (query or "").strip())
        if len(cleaned_query) < 2:
            return []

        fields = [
            ("openfda.generic_name", "generic", "generic_name"),
            ("openfda.substance_name", "substance", "substance_name"),
            ("openfda.brand_name", "brand", "brand_name"),
        ]
        priority = {"generic": 0, "substance": 1, "brand": 2}
        suggestions: Dict[str, Dict[str, Any]] = {}

        async with httpx.AsyncClient(timeout=15.0) as client:
            for field, kind, openfda_key in fields:
                search_query = FDAClient.autocomplete_query(field, cleaned_query)
                if not search_query:
                    continue

                response = await FDAClient.get_label_page(client, search_query, limit=25, skip=0)
                if response.status_code == 404:
                    continue
                if response.status_code != 200:
                    continue

                for entry in response.json().get("results", []) or []:
                    names = entry.get("openfda", {}).get(openfda_key, []) or []
                    if not isinstance(names, list):
                        names = [names]

                    for raw_name in names:
                        display_name = re.sub(r"\s+", " ", str(raw_name or "").strip())
                        if len(display_name) < 2:
                            continue

                        starts_with_query = display_name.lower().startswith(cleaned_query.lower())
                        contains_query = cleaned_query.lower() in display_name.lower()
                        if not starts_with_query and not contains_query:
                            continue

                        key = FDAClient._suggestion_key(display_name)
                        if not key:
                            continue

                        existing = suggestions.get(key)
                        if not existing:
                            suggestions[key] = {
                                "name": display_name,
                                "kind": kind,
                                "matched_field": field,
                                "label_count": 1,
                            }
                        else:
                            existing["label_count"] += 1
                            if priority[kind] < priority[existing["kind"]]:
                                existing["kind"] = kind
                                existing["matched_field"] = field
                            if len(display_name) < len(existing["name"]):
                                existing["name"] = display_name

        ranked = sorted(
            suggestions.values(),
            key=lambda item: (
                not item["name"].lower().startswith(cleaned_query.lower()),
                priority[item["kind"]],
                item["name"].lower(),
            ),
        )

        return [DrugSuggestion(**item) for item in ranked[:limit]]

    @staticmethod
    async def get_label_page(
        client: httpx.AsyncClient,
        search_query: str,
        limit: int,
        skip: int,
    ) -> httpx.Response:
        last_error: Optional[Exception] = None

        for attempt in range(FDAClient.MAX_ATTEMPTS):
            try:
                response = await client.get(
                    FDAClient.BASE_URL,
                    params=FDAClient.request_params(search_query, limit, skip),
                )
                if response.status_code not in FDAClient.RETRY_STATUS_CODES:
                    return response
            except httpx.RequestError as exc:
                last_error = exc

            if attempt < FDAClient.MAX_ATTEMPTS - 1:
                await asyncio.sleep(0.4 * (2 ** attempt))

        if last_error:
            raise last_error

        return response

    @staticmethod
    async def fetch_label_entries(
        client: httpx.AsyncClient,
        search_query: str,
        max_records: int,
        limit: int = 100,
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any], Optional[int]]:
        skip = 0
        all_entries: List[Dict[str, Any]] = []
        meta_info: Dict[str, Any] = {}

        while True:
            response = await FDAClient.get_label_page(client, search_query, limit, skip)

            if response.status_code == 404:
                return [], meta_info, None

            if response.status_code != 200:
                return [], meta_info, response.status_code

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

        return all_entries[:max_records], meta_info, None
    
    @staticmethod
    async def search_drug(drug_name: str, include_ai: bool = False) -> DrugResult:
        """Search for a single drug - mirrors your original query logic"""
        max_records = 300  # safety cap to avoid excessive paging
        all_entries: List[Dict[str, Any]] = []
        meta_info: Dict[str, Any] = {}
        matched_by = None
        last_http_error: Optional[int] = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                for search_option in FDAClient.drug_search_queries(drug_name):
                    entries, meta, http_error = await FDAClient.fetch_label_entries(
                        client,
                        search_option["query"],
                        max_records=max_records,
                    )

                    if http_error:
                        last_http_error = http_error
                        continue

                    if entries:
                        all_entries = entries
                        meta_info = meta
                        matched_by = search_option["label"]
                        break
                
                if last_http_error and not all_entries:
                    return DrugResult(
                        drug=drug_name,
                        last_updated='Error',
                        indications_and_usage=f'HTTP error: {last_http_error}',
                        indications=None
                    )

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
                    f"total_candidates={len(all_entries)}, "
                    f"matched_by={matched_by or 'unknown'}"
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
                
                ai_summary = None
                if include_ai:
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
async def search_single_drug(drug_name: str, include_ai: bool = False):
    """Search for a single drug by name"""
    result = await FDAClient.search_drug(drug_name, include_ai=include_ai)
    return result

@app.get("/api/drugs/suggest", response_model=List[DrugSuggestion])
async def suggest_drug_names(q: str = Query(..., min_length=2), limit: int = Query(10, ge=1, le=20)):
    """Autocomplete drug names from OpenFDA label metadata with local deduplication."""
    return await FDAClient.suggest_drugs(q, limit=limit)

@app.get("/api/drugs/search/{drug_name}/stream")
async def search_single_drug_stream(drug_name: str):
    """Search for a single drug with progress updates via SSE"""
    async def event_generator():
        try:
            # Step 1: Searching FDA
            yield f"data: {json.dumps({'step': 'searching', 'message': 'Searching FDA database...', 'status': 'in_progress'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Perform FDA search (simplified inline version)
            search_query = FDAClient.exact_match_query("openfda.generic_name", drug_name)
            limit = 100
            skip = 0
            max_records = 300
            all_entries = []
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                while True:
                    response = await FDAClient.get_label_page(client, search_query, limit, skip)
                    
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
async def search_by_indication_stream(indication: str):
    """Search FDA labels by indication text with live SSE updates"""
    from collections import defaultdict
    import time
    
    async def event_generator():
        try:
            start_time = time.time()
            
            yield f"data: {json.dumps({'type': 'log', 'message': f'🔍 Searching for: {indication}'})}\n\n"
            await asyncio.sleep(0.05)
            
            # Fetch all labels
            search_query = FDAClient.exact_match_query("indications_and_usage", indication)
            limit = 100
            skip = 0
            all_labels = []
            total_available = None
            batch_count = 0
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                while True:
                    batch_count += 1
                    
                    yield f"data: {json.dumps({'type': 'log', 'message': f'📦 Fetching batch {batch_count} (skip={skip}, limit={limit})...'})}\n\n"
                    
                    response = await FDAClient.get_label_page(client, search_query, limit, skip)
                    
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
            
            yield f"data: {json.dumps({'type': 'log', 'message': '🔬 Summarizing labels...'})}\n\n"

            results = []
            for drug_name, labels in drugs_map.items():
                results.append({
                    'drug_name': drug_name,
                    'total_labels': len(labels),
                    'latest_date': get_latest_date(labels),
                    'brand_names': extract_brand_names(labels),
                    'has_monotherapy': detect_monotherapy(labels),
                    'has_adjunctive': detect_adjunctive(labels),
                })
            
            yield f"data: {json.dumps({'type': 'log', 'message': f'   ✓ Summarized {len(results)} drugs'})}\n\n"
            
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
async def search_by_indication(indication: str):
    """Search FDA labels by indication text, group by drug (non-streaming)"""
    from collections import defaultdict
    
    import time
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"🔍 [INDICATION SEARCH] Searching for: '{indication}'")
    print(f"{'='*60}")
    
    # Fetch all labels matching the indication
    search_query = FDAClient.exact_match_query("indications_and_usage", indication)
    limit = 100
    skip = 0
    all_labels = []
    total_available = None
    batch_count = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            batch_count += 1
            print(f"  📦 Fetching batch {batch_count} (skip={skip}, limit={limit})...")
            
            response = await FDAClient.get_label_page(client, search_query, limit, skip)
            
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
    
    print(f"\n  🔬 Summarizing labels...")
    results = []
    for drug_name, labels in drugs_map.items():
        results.append({
            'drug_name': drug_name,
            'total_labels': len(labels),
            'latest_date': get_latest_date(labels),
            'brand_names': extract_brand_names(labels),
            'has_monotherapy': detect_monotherapy(labels),
            'has_adjunctive': detect_adjunctive(labels),
        })
    
    print(f"     ✓ Summarized {len(results)} drugs")
    
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
    """Analyze all FDA labels for a drug without inferring active/outdated status."""
    
    # Fetch all labels
    search_query = FDAClient.exact_match_query("openfda.generic_name", drug_name)
    limit = 100
    skip = 0
    max_records = 1000
    all_labels = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            response = await FDAClient.get_label_page(client, search_query, limit, skip)
            
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
    
    def get_first(value):
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def get_list(value):
        if isinstance(value, list):
            return value
        if value:
            return [value]
        return []

    def build_formulation(openfda: Dict[str, Any], brand_name: str, generic_name: Optional[str]) -> str:
        parts = []
        dosage_forms = get_list(openfda.get('dosage_form'))
        routes = get_list(openfda.get('route'))

        if dosage_forms:
            parts.append(', '.join(dosage_forms))
        if routes:
            parts.append(', '.join(routes))

        if parts:
            return ' / '.join(parts)

        normalized_brand = (brand_name or '').strip().lower()
        normalized_generic = (generic_name or '').strip().lower()
        if normalized_brand and normalized_brand not in {'generic', normalized_generic}:
            return f"Product family: {brand_name}"

        return 'Unspecified formulation'

    processed_labels = []
    unique_indications_map = {}
    formulation_keys = set()
    version_keys = set()
    
    for label in all_labels:
        openfda = label.get('openfda', {})
        indications = label.get('indications_and_usage')
        if isinstance(indications, list) and indications:
            indications_text = indications[0]
        elif isinstance(indications, str):
            indications_text = indications
        else:
            indications_text = ""

        effective_time = str(label.get('effective_time', '') or '')
        version = label.get('version', 0)
        set_id = label.get('set_id', '')
        brand_name = get_first(openfda.get('brand_name')) or 'Generic'
        manufacturer = get_first(openfda.get('manufacturer_name')) or 'Unknown'
        generic_name = get_first(openfda.get('generic_name'))
        application_number = get_first(openfda.get('application_number'))
        route = get_list(openfda.get('route'))
        dosage_form = get_list(openfda.get('dosage_form'))
        product_type = get_first(openfda.get('product_type'))
        product_ndc = get_list(openfda.get('product_ndc'))
        formulation = build_formulation(openfda, brand_name, generic_name)

        formulation_keys.add((brand_name, formulation, application_number or '', product_type or ''))
        version_keys.add((set_id, str(version)))
        
        if indications_text:
            normalized = ' '.join(indications_text.split())
            existing = unique_indications_map.get(normalized)
            if not existing:
                unique_indications_map[normalized] = {
                    'text': normalized,
                    'first_date': effective_time,
                    'latest_date': effective_time,
                    'label_count': 1,
                }
            else:
                if effective_time and (not existing['first_date'] or effective_time < existing['first_date']):
                    existing['first_date'] = effective_time
                if effective_time and effective_time > existing['latest_date']:
                    existing['latest_date'] = effective_time
                existing['label_count'] += 1
        
        processed_labels.append({
            'effective_time': effective_time,
            'year': effective_time[:4] if len(effective_time) >= 4 else '',
            'version': version,
            'set_id': set_id,
            'brand_name': brand_name,
            'manufacturer': manufacturer,
            'generic_name': generic_name,
            'application_number': application_number,
            'route': route,
            'dosage_form': dosage_form,
            'product_type': product_type,
            'product_ndc': product_ndc,
            'formulation': formulation,
            'indications_text': indications_text
        })
    
    unique_indications = list(unique_indications_map.values())
    unique_indications.sort(key=lambda x: (x['first_date'] or '', len(x['text'])))
    
    return {
        'drug_name': drug_name,
        'total_labels': len(all_labels),
        'labels_with_indications': len([label for label in processed_labels if label['indications_text']]),
        'formulation_count': len(formulation_keys),
        'version_count': len(version_keys),
        'unique_indications': unique_indications,
        'labels': processed_labels
    }

@app.post("/api/drugs/extract-indication-history")
async def extract_indication_history(request: IndicationHistoryRequest):
    """Use OpenAI to normalize indication sections and identify first/latest presence."""
    api_key = (request.api_key or os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="Provide an OpenAI API key or configure OPENAI_API_KEY")

    try:
        from openai import OpenAI
    except ImportError:
        raise HTTPException(status_code=500, detail="OpenAI Python package is not installed")

    labels = []
    for label in request.labels:
        indications_text = (label.get('indications_text') or '').strip()
        if not indications_text:
            continue

        labels.append({
            "effective_time": label.get("effective_time"),
            "year": label.get("year"),
            "version": label.get("version"),
            "set_id": label.get("set_id"),
            "brand_name": label.get("brand_name"),
            "manufacturer": label.get("manufacturer"),
            "generic_name": label.get("generic_name"),
            "application_number": label.get("application_number"),
            "route": label.get("route", []),
            "dosage_form": label.get("dosage_form", []),
            "product_type": label.get("product_type"),
            "product_ndc": label.get("product_ndc", []),
            "formulation": label.get("formulation"),
            "indications_text": indications_text,
        })

    if not labels:
        raise HTTPException(status_code=400, detail="No indication sections were supplied")

    labels.sort(key=lambda item: (str(item.get("effective_time") or ""), str(item.get("version") or "")))

    latest_date = max((str(label.get("effective_time") or "") for label in labels), default="")
    latest_labels = [label for label in labels if label.get("effective_time") == latest_date] if latest_date else []

    sections_by_text: Dict[str, Dict[str, Any]] = {}
    for label in labels:
        normalized_text = ' '.join((label.get("indications_text") or "").split())
        if not normalized_text:
            continue

        section = sections_by_text.setdefault(normalized_text, {
            "indications_text": normalized_text,
            "first_effective_time": label.get("effective_time"),
            "latest_effective_time": label.get("effective_time"),
            "labels": [],
        })

        effective_time = str(label.get("effective_time") or "")
        if effective_time and (not section["first_effective_time"] or effective_time < section["first_effective_time"]):
            section["first_effective_time"] = effective_time
        if effective_time and effective_time > section["latest_effective_time"]:
            section["latest_effective_time"] = effective_time

        section["labels"].append({
            "effective_time": label.get("effective_time"),
            "year": label.get("year"),
            "version": label.get("version"),
            "set_id": label.get("set_id"),
            "brand_name": label.get("brand_name"),
            "application_number": label.get("application_number"),
            "route": label.get("route", []),
            "dosage_form": label.get("dosage_form", []),
            "formulation": label.get("formulation"),
        })

    indication_sections = sorted(
        sections_by_text.values(),
        key=lambda item: (str(item.get("first_effective_time") or ""), str(item.get("latest_effective_time") or "")),
    )

    payload = {
        "drug_name": request.drug_name,
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "latest_effective_time": latest_date,
        "source_label_count": len(labels),
        "unique_indication_section_count": len(indication_sections),
        "indication_sections": indication_sections,
    }

    system_prompt = """You extract normalized FDA-labeled indication history from drug label sections.

Return strict JSON only. Do not infer regulatory approval beyond the supplied indication text.

Definitions:
- A single indication is one distinct labeled use, condition, episode/phase, population, and treatment mode.
- Keep formulations separate when route, dosage form, brand, product family/set_id, or application number materially changes the labeled use.
- Version means the supplied SPL label version for a set_id/product family.
- First appearance year is the earliest supplied section/label year where that exact normalized indication is present.
- Still present in latest is true only if the indication is explicitly present in one or more labels whose effective_time equals latest_effective_time.
- If an indication is absent from the latest label set, mark still_present_in_latest false and explain the guardrail basis.

Output schema:
{
  "drug_name": "string",
  "latest_effective_time": "YYYYMMDD",
  "indications": [
    {
      "indication": "string",
      "condition": "string",
      "episode_or_phase": "string or null",
      "treatment_mode": "Monotherapy | Adjunctive | Combination | Maintenance | Other | Unspecified",
      "population": "string or null",
      "formulations": [
        {
          "formulation": "string",
          "route": ["string"],
          "dosage_form": ["string"],
          "brand_names": ["string"],
          "application_numbers": ["string"],
          "set_ids": ["string"],
          "versions_seen": ["string"]
        }
      ],
      "first_appearance_year": "YYYY or null",
      "first_appearance_effective_time": "YYYYMMDD or null",
      "still_present_in_latest": true,
      "latest_presence_effective_time": "YYYYMMDD or null",
      "guardrail_check": "short explanation citing latest label presence/absence"
    }
  ],
  "latest_label_coverage": {
    "latest_effective_time": "YYYYMMDD",
    "latest_label_count": 0,
    "latest_formulations": ["string"]
  },
  "warnings": ["string"]
}"""

    user_prompt = json.dumps(payload, ensure_ascii=False)

    try:
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_INDICATION_MODEL") or "gpt-4o-mini"
        print(
            "[OPENAI INDICATION EXTRACTION] "
            f"model={model} labels={len(labels)} sections={len(indication_sections)} "
            f"payload_chars={len(user_prompt)}"
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=8000,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)
    except json.JSONDecodeError:
        print("[OPENAI INDICATION EXTRACTION] invalid JSON response")
        raise HTTPException(status_code=502, detail="OpenAI returned invalid JSON")
    except Exception as exc:
        print(f"[OPENAI INDICATION EXTRACTION] failed: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=502, detail=f"OpenAI extraction failed: {exc}")

    def normalize_for_match(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()

    def significant_terms(value: str) -> List[str]:
        stopwords = {
            "and", "or", "the", "for", "with", "of", "in", "to", "as", "a", "an",
            "treatment", "therapy", "disorder", "disease", "associated", "patients",
            "adult", "adults", "pediatric", "children",
        }
        return [
            term
            for term in normalize_for_match(value).split()
            if len(term) > 2 and term not in stopwords
        ]

    def label_matches_indication(label: Dict[str, Any], indication: Dict[str, Any]) -> bool:
        label_text = normalize_for_match(label.get("indications_text") or "")
        condition = indication.get("condition") or indication.get("indication") or ""
        condition_terms = significant_terms(condition)
        if condition_terms and not all(term in label_text for term in condition_terms):
            return False

        if not condition_terms:
            indication_terms = significant_terms(indication.get("indication") or "")
            if indication_terms and not all(term in label_text for term in indication_terms[:4]):
                return False

        detail_text = normalize_for_match(
            " ".join([
                str(indication.get("episode_or_phase") or ""),
                str(indication.get("treatment_mode") or ""),
            ])
        )
        required_terms = []
        if "maintenance" in detail_text:
            required_terms.append("maintenance")
        if "adjunctive" in detail_text or "adjunct" in detail_text:
            required_terms.append("adjunct")
        if "monotherapy" in detail_text:
            required_terms.append("monotherapy")
        if "acute" in detail_text:
            required_terms.append("acute")
        if "manic" in detail_text:
            required_terms.append("manic")
        if "mixed" in detail_text:
            required_terms.append("mixed")

        return all(term in label_text for term in required_terms)

    def append_formulation_coverage(indication: Dict[str, Any], matching_labels: List[Dict[str, Any]]) -> None:
        coverage: Dict[str, Dict[str, Any]] = {}
        for existing in indication.get("formulations") or []:
            formulation_name = existing.get("formulation") or "Unspecified formulation"
            coverage[formulation_name] = {
                "formulation": formulation_name,
                "route": set(existing.get("route") or []),
                "dosage_form": set(existing.get("dosage_form") or []),
                "brand_names": set(existing.get("brand_names") or []),
                "application_numbers": set(existing.get("application_numbers") or []),
                "set_ids": set(existing.get("set_ids") or []),
                "versions_seen": set(str(version) for version in (existing.get("versions_seen") or [])),
            }

        for label in matching_labels:
            formulation_name = label.get("formulation") or "Unspecified formulation"
            item = coverage.setdefault(formulation_name, {
                "formulation": formulation_name,
                "route": set(),
                "dosage_form": set(),
                "brand_names": set(),
                "application_numbers": set(),
                "set_ids": set(),
                "versions_seen": set(),
            })
            item["route"].update(label.get("route") or [])
            item["dosage_form"].update(label.get("dosage_form") or [])
            if label.get("brand_name"):
                item["brand_names"].add(label["brand_name"])
            if label.get("application_number"):
                item["application_numbers"].add(label["application_number"])
            if label.get("set_id"):
                item["set_ids"].add(label["set_id"])
            if label.get("version") is not None:
                item["versions_seen"].add(str(label["version"]))

        indication["formulations"] = [
            {
                "formulation": item["formulation"],
                "route": sorted(item["route"]),
                "dosage_form": sorted(item["dosage_form"]),
                "brand_names": sorted(item["brand_names"]),
                "application_numbers": sorted(item["application_numbers"]),
                "set_ids": sorted(item["set_ids"]),
                "versions_seen": sorted(item["versions_seen"], key=lambda value: (len(value), value)),
            }
            for item in sorted(coverage.values(), key=lambda value: value["formulation"])
        ]

    for indication in parsed.get("indications") or []:
        matching_labels = [
            label
            for label in labels
            if label_matches_indication(label, indication)
        ]
        if matching_labels:
            append_formulation_coverage(indication, matching_labels)

    parsed.setdefault("drug_name", request.drug_name)
    parsed.setdefault("latest_effective_time", latest_date)
    parsed.setdefault("latest_label_coverage", {
        "latest_effective_time": latest_date,
        "latest_label_count": len(latest_labels),
        "latest_formulations": sorted({label.get("formulation") or "Unspecified formulation" for label in latest_labels}),
    })
    parsed["payload_label_count"] = len(labels)
    parsed["payload_section_count"] = len(indication_sections)
    return parsed

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
                max_tokens=8000,
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
                        "max_tokens": 8000,
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
                        max_output_tokens=8000,  # Increased for complex drugs with many indications
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
