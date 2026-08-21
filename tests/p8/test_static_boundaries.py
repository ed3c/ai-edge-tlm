from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PUBLIC=[ROOT/'apps',ROOT/'tests/p8']

def test_no_private_workspace_literals_or_provider_sdk_leakage():
    forbidden=['docs'+'.google'+'.com','drive'+'.google'+'.com','CODEXDOC_'+'CONTROL_PLANE_'+'URI'+'=','CODEXDOC_'+'LEDGER_'+'URI'+'=']
    allowed_ext={'.py','.kt','.swift','.md','.json'}
    text='\n'.join(p.read_text(errors='ignore') for root in PUBLIC for p in root.rglob('*') if p.is_file() and p.suffix in allowed_ext)
    for item in forbidden: assert item not in text
    for sdk_symbol in ['LanguageModelSession','LlmInference','LiteRtLm','MediaPipeTasksGenAI']:
        assert sdk_symbol not in (ROOT/'apps/android-reference/src/main/kotlin/io/ed3c/aiedge/reference/ReferenceHost.kt').read_text()
