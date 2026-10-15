import tempfile, unittest
from pathlib import Path
from core_federation.store import submit,get,propose_edge
class FederationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=Path(self.tmp.name)/'state.sqlite3'
  self.msg={'transaction_id':'T1','from_core':'EPI-CORE','to_core':'ENTIDAD CORE','operation':'represent','payload':{'claim':'Existe una afirmación'},'schema_version':'0.2.0'}
 def tearDown(self):self.tmp.cleanup()
 def test_roundtrip_reopen(self):
  self.assertEqual(submit(self.db,self.msg)['state'],'RECORDED');self.assertEqual(get(self.db,'T1'),self.msg)
 def test_idempotent(self):
  submit(self.db,self.msg);self.assertEqual(submit(self.db,self.msg)['state'],'ALREADY_RECORDED')
 def test_collision(self):
  submit(self.db,self.msg);bad=dict(self.msg,payload={'claim':'otra'})
  with self.assertRaises(ValueError):submit(self.db,bad)
 def test_unknown_core(self):
  with self.assertRaises(ValueError):submit(self.db,dict(self.msg,to_core='GHOST'))
 def test_unknown_version(self):
  with self.assertRaises(ValueError):submit(self.db,dict(self.msg,schema_version='0.9.9'))
 def test_edge_requires_transaction(self):
  e={'id':'E1','source_core':'EPI-CORE','source_id':'a','predicate':'respalda','target_core':'ENTIDAD CORE','target_id':'b','status':'PROPUESTO','evidence':[],'origin':'user','transaction_id':'T1'}
  with self.assertRaises(ValueError):propose_edge(self.db,e)
  submit(self.db,self.msg);self.assertEqual(propose_edge(self.db,e)['state'],'CANDIDATA')
 def test_no_self_accepted_edge(self):
  submit(self.db,self.msg)
  e={'id':'E1','source_core':'EPI-CORE','source_id':'a','predicate':'respalda','target_core':'ENTIDAD CORE','target_id':'b','status':'RESPALDADO','evidence':[],'origin':'user','transaction_id':'T1','review_state':'ACEPTADA'}
  with self.assertRaises(ValueError):propose_edge(self.db,e)
if __name__=='__main__':unittest.main()
