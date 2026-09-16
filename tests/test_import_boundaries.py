import subprocess
import sys


def test_import_does_not_load_rendering_engines():
    code = "import sys, utterplan; print(sorted(x for x in sys.modules if x in {'pykokoro','kokorog2p','piperg2p','onnxruntime','numpy','soundfile'}))"
    result = subprocess.run(
        [sys.executable, "-c", code], check=True, capture_output=True, text=True
    )
    assert result.stdout.strip() == "[]"
