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
from datetime import datetime

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
        url = f'{FDAClient.BASE_URL}?search=openfda.generic_name:"{drug_name}"&limit=1'
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'results' in data and data['results']:
                        entry = data['results'][0]
                        last_updated = data['meta'].get('last_updated', 'N/A')
                        
                        # Extract comprehensive drug information
                        openfda = entry.get('openfda', {})
                        indications_text = entry.get('indications_and_usage', ['Not found'])
                        indications_text = indications_text[0] if isinstance(indications_text, list) and indications_text else (indications_text or 'Not found')
                        extracted_indications = extract_indications(indications_text)
                        
                        return DrugResult(
                            drug=drug_name,
                            last_updated=last_updated,
                            indications_and_usage=indications_text,
                            indications=extracted_indications if extracted_indications else None,
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
                    else:
                        return DrugResult(
                            drug=drug_name,
                            last_updated='N/A',
                            indications_and_usage='No data found',
                            indications=None
                        )
                else:
                    return DrugResult(
                        drug=drug_name,
                        last_updated='Error',
                        indications_and_usage=f'HTTP error: {response.status_code}',
                        indications=None
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