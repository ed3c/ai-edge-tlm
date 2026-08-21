import os, subprocess
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
@pytest.mark.skipif(os.environ.get('AI_EDGE_RUN_NATIVE_TOOLCHAINS')!='1',reason='LOCAL native toolchain lane')
def test_cross_platform_native_golden():
    subprocess.run([str(ROOT/'tests/p8/run_cross_platform_golden.sh')],cwd=ROOT,check=True)
