"""M7 harness skeleton. Connect a real model runner before execution."""
import json
from pathlib import Path

CONTRACT=Path(__file__).with_name("m7_contract.json")

def run_branch(model_runner, tasks, kbs_context=None):
    outputs=[]
    for task in tasks:
        prompt=task["prompt"]
        if kbs_context is not None:
            prompt=prompt+"\n\nKBS CONTEXT:\n"+kbs_context(task)
        outputs.append(model_runner(prompt))
    return outputs

def main():
    contract=json.loads(CONTRACT.read_text())
    raise SystemExit("M7 NOT EXECUTED: configure one real model_runner for both branches, then run reserved tasks.")

if __name__=="__main__":
    main()
