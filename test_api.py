"""
test_api.py — Suite de pruebas automatizadas para los 15 API Endpoints SOTA del SaaS.
"""

import unittest
from fastapi.testclient import TestClient
from agent.api_server import app

client = TestClient(app)

class TestSaaSAPI(unittest.TestCase):
    """Verificación de los 15 API Endpoints."""

    def test_00_health(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_01_build_mece_tree(self):
        payload = {
            "text_corpus": "El procesamiento del lenguaje natural requiere lematización y clustering coseno.",
            "tau_threshold": 0.25,
            "max_depth_k": 3
        }
        response = client.post("/api/v2/ontology/build-mece-tree", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("tree_render", data)

    def test_02_sat_verify_execution(self):
        payload = {
            "knowledge_base_jsonld": {"@context": "http://www.w3.org/2004/02/skos/core#"},
            "action_proposition": "extraer sintagma nominal"
        }
        response = client.post("/api/v2/sat/verify-execution", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_satisfiable"])

    def test_03_agm_belief_revision(self):
        payload = {
            "knowledge_base_jsonld": {},
            "fact": "el lema de sintagmas es sintagma",
            "operation": "insert"
        }
        response = client.post("/api/v2/agm/belief-revision", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["epistemic_closure"])

    def test_04_pharmacogenomics_align(self):
        payload = {
            "alleles": ["CYP2D6*4", "CYP2D6*1"],
            "drug_id": "codeine"
        }
        response = client.post("/api/v2/pharmacogenomics/align-phenotype", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Poor Metabolizer", response.json()["phenotype_classification"])

    def test_05_regtech_audit_contract(self):
        payload = {
            "contract_text": "El proveedor debe garantizar la canonicalización WSD y el filtrado morfosintáctico.",
            "regulatory_standard": "ISO 24613"
        }
        response = client.post("/api/v2/regtech/audit-contract", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["compliance_score"], 0)

    def test_06_tool_grammar_gen(self):
        payload = {
            "api_spec_json": {
                "paths": {
                    "/users": {
                        "get": {"operationId": "get_users", "summary": "List users"}
                    }
                }
            }
        }
        response = client.post("/api/v2/agent/tool-grammar-gen", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_tools_generated"], 1)

    def test_07_wsd_disambiguate(self):
        payload = {
            "terms": ["clase", "nodo"],
            "context": "programación orientada a objetos"
        }
        response = client.post("/api/v2/wsd/disambiguate-entities", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["disambiguated_entities"]), 2)

    def test_08_graphrag_extract_subgraph(self):
        payload = {
            "query": "clustering por similitud coseno",
            "tau_threshold": 0.25
        }
        response = client.post("/api/v2/graphrag/extract-subgraph", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("subgraph_nodes", response.json())

    def test_09_aero_maintenance_validation(self):
        payload = {
            "manual_step": "Inspeccionar válvula de alivio",
            "system_state": {"pressure_relieved": True}
        }
        response = client.post("/api/v2/aero/maintenance-validation", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["execution_permitted"])

    def test_10_cyber_soar_check(self):
        payload = {
            "playbook_steps": ["Escanear subred 192.168.1.0/24", "Aislar servidor de prod principal"]
        }
        response = client.post("/api/v2/cyber/soar-playbook-check", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["playbook_validity"], "UNSAT_CONFLICT")

    def test_11_kyc_logic_evaluator(self):
        payload = {
            "user_profile": {"user_id": "usr_99", "risk_score": 20, "identity_verified": True}
        }
        response = client.post("/api/v2/fintech/kyc-logic-evaluator", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["kyc_passed"])

    def test_12_ontology_diff(self):
        payload = {
            "old_kb": {"node1": "v1"},
            "new_kb": {"node1": "v1", "node2": "v2"}
        }
        response = client.post("/api/v2/ontology/diff-export", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["added_nodes_count"], 1)

    def test_13_context_compressor(self):
        payload = {
            "raw_prompt": "Por favor realiza una extracción detallada y minería léxica sobre este corpus para obtener el árbol MECE."
        }
        response = client.post("/api/v2/llm/context-compressor", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("compressed_imperative_prompt", response.json())

    def test_14_trial_eligibility(self):
        payload = {
            "patient_emr": {"patient_id": "pat_01", "age": 45, "conditions": ["Diabetes Type II"]},
            "trial_criteria": ["18 <= Age <= 75"]
        }
        response = client.post("/api/v2/clinical/trial-eligibility", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_eligible"])

    def test_15_sat_explain_unfeasibility(self):
        payload = {
            "conflict_clauses": [["ACTION_ISOLATE", "NOT_PROD"], ["ACTION_ISOLATE", "PROD"]]
        }
        response = client.post("/api/v2/sat/explain-unfeasibility", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("natural_language_explanation", response.json())

    def test_16_gui_perceive(self):
        payload = {
            "text_content_to_diagnose": "ERROR: Build failed 2 minutes ago"
        }
        response = client.post("/api/v2/agent/gui-perceive", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(len(data["detected_errors"]), 1)


if __name__ == "__main__":
    unittest.main()
