import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_input_subjects_keep_real_and_private_lanes_open():
    x=json.loads((ROOT/'training/receipts/p7-input-subjects.json').read_text())
    assert x['p4']['commit']=='6b90db1654d10cd34ad093890af4209daf810b7d'
    assert x['real_model_terms']=='HUMAN_ADMIT_REQUIRED'
    assert x['private_dataset']=='PRIVATE_NOT_EXERCISED'
    assert x['p3c_runtime'].startswith('BLOCKED')

def test_vendor_numbers_are_not_embedded_as_local_results():
    text=''.join(p.read_text() for p in (ROOT/'training').rglob('*') if p.is_file() and p.suffix in {'.py','.md','.json'})
    assert '1916 tokens' not in text and '142 tokens' not in text and '90%+' not in text
