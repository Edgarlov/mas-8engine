"""
MAS-8ENGINE │ test_drive_taxonomies.py
Pruebas unitarias para los algoritmos extraídos de Google Drive:
- Horvitz-Thompson Estimator
- UCB1 Selector
- C-Value Term Extraction
"""
import pytest
from engines.horvitz_thompson_sampler import HorvitzThompsonEstimator, SampleNode, UCB1Selector
from pipeline.c_value_extractor import CValueExtractor


def test_horvitz_thompson_estimation():
    samples = [
        SampleNode(node_id="n1", value=10.0, inclusion_prob=0.5),
        SampleNode(node_id="n2", value=20.0, inclusion_prob=0.25),
        SampleNode(node_id="n3", value=15.0, inclusion_prob=0.5)
    ]
    res = HorvitzThompsonEstimator.estimate_total(samples)
    
    # 10/0.5 + 20/0.25 + 15/0.5 = 20 + 80 + 30 = 130.0
    assert res.estimated_total == 130.0
    assert res.sample_size == 3
    assert res.confidence_interval_95[1] >= res.estimated_total


def test_ucb1_node_selection():
    nodes = [
        {"node_id": "child_1", "avg_reward": 0.8, "visits": 10},
        {"node_id": "child_2", "avg_reward": 0.5, "visits": 2},
        {"node_id": "child_3", "avg_reward": 0.9, "visits": 0}  # Unvisited should get infinity score
    ]
    best = UCB1Selector.select_best_node(nodes, parent_total_visits=12)
    assert best["node_id"] == "child_3"


def test_c_value_extraction():
    text = (
        "El motor de inteligencia artificial utiliza redes neuronales artificiales "
        "y procesamiento de lenguaje natural. Las redes neuronales artificiales son fundamentales."
    )
    results = CValueExtractor.compute_c_values(text, min_freq=1)
    
    assert len(results) > 0
    top_term = results[0]
    assert top_term.c_value >= 0.0
    assert top_term.word_count >= 2
