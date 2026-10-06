import unittest
from src.kbs_tech.core import KBS

class TestKBS(unittest.TestCase):
    def test_selective_impact(self):
        k=KBS(
          {"K1":{"status":"RESPALDADO","source":"S1","active":True},"K2":{"status":"RESPALDADO","source":"S2","active":True}},
          {"I1":{"status":"INFERIDO","premises":["K1","K2"],"active":True}}
        )
        e=k.remove_source("S1","E1")
        self.assertEqual(e["affected"],["K1"])
        self.assertEqual(e["dependent"],["I1"])
        self.assertEqual(e["truth"],"NOT_DETERMINED")
        self.assertEqual(k.remove_source("S1","E1")["effect"],"NOOP_REPLAY")

if __name__=="__main__":
    unittest.main()
