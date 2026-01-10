from datasets import load_dataset

def load_and_slice_datasets():
    print("Downloading Datasets...")
    # 1. Personal Data (nvidia/Nemotron-Personas-USA)
    ds_personal = load_dataset("nvidia/Nemotron-Personas-USA", split="train")
    # Take first 1000
    personal_subset = ds_personal.select(range(min(1000, len(ds_personal))))
    
    # 2. CVE Data (stasvinokur/cve-and-cwe-dataset-1999-2025)
    ds_cve = load_dataset("stasvinokur/cve-and-cwe-dataset-1999-2025", split="train")
    # Take last 2000
    total_cve = len(ds_cve)
    cve_subset = ds_cve.select(range(max(0, total_cve - 2000), total_cve))
    
    print(f"Loaded: {len(personal_subset)} Personal records, {len(cve_subset)} CVE records.")
    return personal_subset, cve_subset

def prepare_documents(personal_subset, cve_subset):
    documents = []
    metadatas = []
    ids = []

    print("Processing Personal Data...")
    for i, item in enumerate(personal_subset):
        # Clean up the persona text to avoid context bloat
        # Ingesting ALL fields as requested to ensure complete context
        text_parts = [
            f"PERSONAL DATA RECORD:",
            f"UUID: {item.get('uuid', 'N/A')}",
            f"Name/Identity: {item.get('professional_persona', '').split(' works as ')[0] if ' works as ' in item.get('professional_persona', '') else 'Unknown'}", # Heuristic to extract name if possible, or just rely on UUID/Context
            f"Age: {item.get('age', 'N/A')}",
            f"Sex: {item.get('sex', 'N/A')}",
            f"Marital Status: {item.get('marital_status', 'N/A')}",
            f"Occupation: {item.get('occupation', 'N/A')}",
            f"Location: {item.get('city', 'N/A')}, {item.get('state', 'N/A')}",
            f"Education: {item.get('education_level', 'N/A')}",
            f"Cultural Background: {item.get('cultural_background', 'N/A')}",
            f"Professional Persona: {item.get('professional_persona', 'N/A')}",
            f"Skills: {item.get('skills_and_expertise', 'N/A')}",
            f"Sports Persona: {item.get('sports_persona', 'N/A')}",
            f"Arts Persona: {item.get('arts_persona', 'N/A')}",
            f"Travel Persona: {item.get('travel_persona', 'N/A')}",
            f"Culinary Persona: {item.get('culinary_persona', 'N/A')}"
        ]
        full_text = "\n".join(text_parts)
        
        documents.append(full_text)
        metadatas.append({"source": "personal_sensitive", "type": "pii", "id": item.get('uuid')})
        ids.append(f"pii_{i}")

    print("Processing CVE Data...")
    for i, item in enumerate(cve_subset):
        cve_id = item.get('CVE-ID', 'N/A')
        cwe_id = item.get('CWE-ID', 'N/A')
        cvss_v2 = item.get('CVSS-V2', 'N/A')
        cvss_v3 = item.get('CVSS-V3', 'N/A')
        cvss_v4 = item.get('CVSS-V4', 'N/A')
        desc = item.get('DESCRIPTION', 'N/A')
        severity = item.get('SEVERITY', 'N/A')
        
        text = f"CVE SECURITY RECORD:\nID: {cve_id}\nCWE: {cwe_id}\nCVSS V2: {cvss_v2}\nCVSS V3: {cvss_v3}\nCVSS V4: {cvss_v4}\nSeverity: {severity}\nDescription: {desc}"
        
        documents.append(text)
        metadatas.append({"source": "cve_public", "type": "security", "id": cve_id})
        ids.append(f"cve_{i}")
        
    return documents, metadatas, ids
