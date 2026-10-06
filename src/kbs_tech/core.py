from copy import deepcopy

ALLOWED={"RESPALDADO","INFERIDO","PROPUESTO","INCIERTO","DESCONOCIDO"}

class KBS:
    def __init__(self, claims, inferences):
        self.claims=deepcopy(claims)
        self.inferences=deepcopy(inferences)
        self.history=[]
    def explain(self, item_id):
        x=self.claims.get(item_id) or self.inferences.get(item_id)
        if not x: return None
        return {"id":item_id,"status":x["status"],"source":x.get("source"),"premises":x.get("premises",[]),"active":x.get("active",True)}
    def remove_source(self, source, event_id):
        if any(e["event_id"]==event_id for e in self.history):
            return {"effect":"NOOP_REPLAY"}
        affected=[]
        for cid,c in self.claims.items():
            if c.get("source")==source and c.get("active",True):
                c["active"]=False;c["status"]="INCIERTO";affected.append(cid)
        dependent=[]
        for iid,inf in self.inferences.items():
            if any(p in affected for p in inf.get("premises",[])):
                inf["active"]=False;inf["status"]="INCIERTO";dependent.append(iid)
        event={"event_id":event_id,"affected":affected,"dependent":dependent,"truth":"NOT_DETERMINED"}
        self.history.append(event)
        return event
