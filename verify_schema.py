"""Verify JSON-LD schema completeness"""
import json

with open('schemas/ontologia_v2_full.json', encoding='utf-8') as f:
    data = json.load(f)

def count_nodes(nodes):
    total = 0
    atomic = 0
    for n in nodes:
        total += 1
        children = n.get('skos:narrower', [])
        if not children:
            atomic += 1
        else:
            t, a = count_nodes(children)
            total += t
            atomic += a
    return total, atomic

graph = data.get('@graph', data.get('skos:hasTopConcept', []))
total, atomic = count_nodes(graph)
print(f"Top-level items in @graph: {len(graph)}")
print(f"Total nodes (recursive):   {total}")
print(f"Atomic nodes (leaf):       {atomic}")
meta = data.get('_meta', {})
print(f"Meta claims total={meta.get('total_nodes')}, atomic={meta.get('atomic_nodes')}")
print(f"MECE compliant: {meta.get('mece_compliant')}")
print(f"SAT KB:         {meta.get('sat_kb')}")

# Sample 3 atomic nodes
def find_atomic(nodes, found=None):
    if found is None:
        found = []
    for n in nodes:
        children = n.get('skos:narrower', [])
        if not children and len(found) < 3:
            found.append(n)
        else:
            find_atomic(children, found)
    return found

print("\nSample atomic nodes:")
for n in find_atomic(graph):
    print(f"  [{n['skos:notation']}] {n['skos:prefLabel'][:55]}")
    print(f"    imperative: {n.get('owl:imperative','N/A')[:60]}")
    print(f"    uuid:       {n.get('owl:hasKey','N/A')}")
    print(f"    logic:      {n.get('_logic','N/A')[:60]}")
    print()
