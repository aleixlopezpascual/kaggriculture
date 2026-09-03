"""Extracts and decodes competitor agents using their exact base85-zlib decoding logic."""

import json
import base64
import zlib
from pathlib import Path


def extract_v14():
    notebook_path = Path("competitors/notebooks/84-84-base-public-holdout-v14-clone-preemption.ipynb")
    out_path = Path("competitors/notebooks/v14_main.py")
    print(f"Extracting V14 Agent from {notebook_path}...")

    with open(notebook_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Search for _AGENT_B85_PARTS in the cells
    b85_parts = []
    for cell in data["cells"]:
        source = cell.get("source", [])
        source_str = "".join(source)
        if "_AGENT_B85_PARTS" in source_str:
            # Let's extract the list of strings
            # We can use safe evaluation or safe exec to get _AGENT_B85_PARTS
            local_vars = {}
            try:
                exec(source_str, {}, local_vars)
            except Exception:
                pass
            b85_parts = local_vars.get("_AGENT_B85_PARTS")
            if b85_parts:
                break

    if not b85_parts:
        print("Failed to find _AGENT_B85_PARTS inside V14 notebook cells.")
        return False

    # Decode and decompress
    try:
        agent_bytes = zlib.decompress(base64.b85decode("".join(b85_parts).encode("ascii")))
        agent_src = agent_bytes.decode("utf-8")
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(agent_src)
        print(f"Successfully extracted V14 agent to {out_path} ({len(agent_src)} chars).")
        return True
    except Exception as e:
        print(f"Failed to decode/decompress V14 agent: {e}")
    return False


def extract_v27():
    notebook_path = Path("competitors/notebooks/25-27-strict-future-v27-midgame-meta-reset.ipynb")
    out_path = Path("competitors/notebooks/v27_main.py")
    print(f"Extracting V27 Agent from {notebook_path}...")

    with open(notebook_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Search for _AGENT_B85_PARTS in the cells
    b85_parts = []
    for cell in data["cells"]:
        source = cell.get("source", [])
        source_str = "".join(source)
        if "_AGENT_B85_PARTS" in source_str:
            local_vars = {}
            try:
                exec(source_str, {}, local_vars)
            except Exception:
                pass
            b85_parts = local_vars.get("_AGENT_B85_PARTS")
            if b85_parts:
                break

    if not b85_parts:
        print("Failed to find _AGENT_B85_PARTS inside V27 notebook cells.")
        return False

    # Decode and decompress
    try:
        agent_bytes = zlib.decompress(base64.b85decode("".join(b85_parts).encode("ascii")))
        agent_src = agent_bytes.decode("utf-8")
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(agent_src)
        print(f"Successfully extracted V27 agent to {out_path} ({len(agent_src)} chars).")
        return True
    except Exception as e:
        print(f"Failed to decode/decompress V27 agent: {e}")
    return False


def extract_bruceqdu():
    notebook_path = Path("competitors/notebooks/my-2026-08-04-high-score-pipeline.ipynb")
    out_path = Path("competitors/notebooks/bruceqdu_main.py")
    print(f"Extracting Bruceqdu Agent from {notebook_path}...")

    with open(notebook_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Cell 0 has AGENT_SOURCE
    source_str = "".join(data["cells"][0]["source"])
    local_vars = {}
    
    class MockPath:
        def __init__(self, *args, **kwargs): pass
        def write_bytes(self, *args, **kwargs): pass
    
    safe_globals = {
        "Path": MockPath,
        "hashlib": type("mock", (), {"sha256": lambda *args: type("mock2", (), {"hexdigest": lambda: ""})()}),
        "tarfile": type("mock", (), {"open": lambda *args, **kwargs: type("mock2", (), {"__enter__": lambda s: s, "__exit__": lambda *args: None, "addfile": lambda *args: None})()})
    }
    
    try:
        exec(source_str, safe_globals, local_vars)
        agent_src = local_vars.get("AGENT_SOURCE")
        if agent_src:
            with open(out_path, "w", encoding="utf-8") as out:
                out.write(agent_src)
            print(f"Successfully extracted Bruceqdu agent to {out_path} ({len(agent_src)} chars).")
            return True
    except Exception as e:
        print(f"Failed to extract Bruceqdu: {e}")
    return False


def main():
    v14_ok = extract_v14()
    v27_ok = extract_v27()
    bruce_ok = extract_bruceqdu()
    
    print("\nExtraction Results:")
    print(f"V14 (Clone Preemption):  {'SUCCESS' if v14_ok else 'FAILED'}")
    print(f"V27 (Midgame Reset):     {'SUCCESS' if v27_ok else 'FAILED'}")
    print(f"Bruceqdu (High-Score):   {'SUCCESS' if bruce_ok else 'FAILED'}")


if __name__ == "__main__":
    main()
