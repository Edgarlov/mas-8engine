import json,sys
from pathlib import Path

def load(p): return json.loads(Path(p).read_text())

def score_record(r):
    # Structural evaluator only; semantic correctness still needs an explicit oracle/judge.
    required=["task_id","branch","model","prompt","output","elapsed_seconds"]
    return {"complete":all(k in r for k in required),"nonempty":bool(r.get("output","").strip())}

def main(path):
    rows=load(path)
    scored=[dict(r,structural=score_record(r)) for r in rows]
    out=Path("artifacts/m7"); out.mkdir(parents=True,exist_ok=True)
    (out/"structural_scores.json").write_text(json.dumps(scored,indent=2))
    if not all(x["structural"]["complete"] and x["structural"]["nonempty"] for x in scored):
        raise SystemExit("FAIL_STRUCTURAL")
    print("STRUCTURAL_PASS; semantic A/B judgment still required.")

if __name__=="__main__": main(sys.argv[1])
