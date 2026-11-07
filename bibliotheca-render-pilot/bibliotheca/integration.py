"""SCI-CAP integration: explicit federation registry and evidence-grounded claims.
Local authenticated prototype; registration does not enable hosted access.
"""
import json, time, uuid
from .service import MemoryService

STATES={'hypothesis','inferred','observed','unknown','refuted'}
REVIEWS={'supported','challenged','inconclusive'}

class UniversityMemory(MemoryService):
    def __init__(self,root):
        super().__init__(root)
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS units (id TEXT PRIMARY KEY,kind TEXT NOT NULL CHECK(kind IN ('faculty','chair','agent','team')), title TEXT NOT NULL, parent TEXT REFERENCES units(id), status TEXT NOT NULL DEFAULT 'registered', created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS affiliations (unit_id TEXT NOT NULL REFERENCES units(id),principal TEXT NOT NULL REFERENCES principals(id), role TEXT NOT NULL, PRIMARY KEY(unit_id,principal));
        CREATE TABLE IF NOT EXISTS propositions (id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES principals(id),statement TEXT NOT NULL,epistemic TEXT NOT NULL, uncertainty REAL,uncertainty_basis TEXT,created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS evidence_records (id TEXT PRIMARY KEY,claim_id TEXT NOT NULL REFERENCES propositions(id),doc_id TEXT NOT NULL REFERENCES docs(id),locator TEXT NOT NULL,method TEXT NOT NULL,relationship TEXT NOT NULL CHECK(relationship IN ('supports','contradicts','context')),contributor TEXT NOT NULL REFERENCES principals(id),created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY,claim_id TEXT NOT NULL REFERENCES propositions(id),reviewer TEXT NOT NULL REFERENCES principals(id),finding TEXT NOT NULL,reason TEXT NOT NULL,created REAL NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_evidence_claim ON evidence_records(claim_id);
        ''')
        self.db.commit()

    def register_unit(self, token, unit_id, kind, title, parent=None):
        actor=self.authenticate(token);self.require_admin(actor)
        if kind not in {'faculty','chair','agent','team'} or not unit_id.strip() or not title.strip():raise ValueError('invalid unit')
        with self.db:
            self.db.execute('INSERT INTO units(id,kind,title,parent,created) VALUES(?,?,?,?,?)',(unit_id,kind,title,parent,time.time()))
            self._event('unit-registered',actor,unit_id,{'kind':kind,'parent':parent})
        return {'unit_id':unit_id,'status':'registered','connected':False}

    def affiliate(self,token,unit_id,principal,role='member'):
        actor=self.authenticate(token);self.require_admin(actor)
        if not self.db.execute('SELECT 1 FROM principals WHERE id=? AND disabled=0',(principal,)).fetchone():raise ValueError('unknown principal')
        with self.db:
            self.db.execute('INSERT INTO affiliations(unit_id,principal,role) VALUES (?,?,?)',(unit_id,principal,role))
            self._event('affiliated',actor,unit_id,{'principal':principal,'role':role})
        return {'unit_id':unit_id,'principal':principal,'role':role,'connected':False}

    def units_for(self,token):
        actor=self.authenticate(token)
        if actor=='rectoria': return [dict(r) for r in self.db.execute('SELECT * FROM units ORDER BY id')]
        return [dict(r) for r in self.db.execute('SELECT u.* FROM units u JOIN affiliations a ON a.unit_id=u.id WHERE a.principal=?',(actor,))]

    def assert_claim(self,token,statement,epistemic='hypothesis',uncertainty=None,uncertainty_basis=None):
        actor=self.authenticate(token)
        if epistemic not in STATES or not statement.strip():raise ValueError('invalid claim')
        if uncertainty is not None and not (0<=uncertainty<=1):raise ValueError('uncertainty must be [0,1]')
        if uncertainty is not None and not uncertainty_basis:raise ValueError('uncertainty requires basis')
        cid='CL-'+uuid.uuid4().hex[:18]
        with self.db:
            self.db.execute('INSERT INTO propositions VALUES (?,?,?,?,?,?,?)',(cid,actor,statement,epistemic,uncertainty,uncertainty_basis,time.time()))
            self._event('claim-asserted',actor,cid,{'epistemic':epistemic})
        return {'claim_id':cid,'status':epistemic,'review':'not_reviewed'}

    def cite(self,token,claim_id,doc_id,locator,method,relationship='supports'):
        actor=self.authenticate(token)
        # Access to the actual object is mandatory before linking it.
        self._doc(doc_id,actor)
        claim=self.db.execute('SELECT * FROM propositions WHERE id=?',(claim_id,)).fetchone()
        if not claim:raise KeyError('unknown claim')
        if claim['owner']!=actor:raise PermissionError('only claim owner may attach initial evidence')
        if not locator.strip() or not method.strip() or relationship not in {'supports','contradicts','context'}:raise ValueError('missing citation details')
        evid='EV-'+uuid.uuid4().hex[:18]
        with self.db:
            self.db.execute('INSERT INTO evidence_records VALUES (?,?,?,?,?,?,?,?)',(evid,claim_id,doc_id,locator,method,relationship,actor,time.time()))
            self._event('evidence-added',actor,claim_id,{'evidence_id':evid,'doc_id':doc_id,'relationship':relationship})
        return {'evidence_id':evid,'claim_id':claim_id,'relationship':relationship,'verified':False}

    def review_claim(self,token,claim_id,finding,reason):
        actor=self.authenticate(token)
        c=self.db.execute('SELECT * FROM propositions WHERE id=?',(claim_id,)).fetchone()
        if not c:raise KeyError('unknown claim')
        if actor==c['owner']:raise PermissionError('reviewer must differ from author')
        if finding not in REVIEWS or not reason.strip():raise ValueError('invalid review')
        refs=self.db.execute('SELECT doc_id FROM evidence_records WHERE claim_id=?',(claim_id,)).fetchall()
        if not refs:raise ValueError('no evidence to review')
        for r in refs:self._doc(r['doc_id'],actor)
        rid='RV-'+uuid.uuid4().hex[:18]
        with self.db:
            self.db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?)',(rid,claim_id,actor,finding,reason,time.time()))
            self._event('claim-reviewed',actor,claim_id,{'review_id':rid,'finding':finding})
        return {'review_id':rid,'finding':finding,'note':'Review is recorded; scientific truth not established by record alone'}

    def dossier(self,token,claim_id):
        actor=self.authenticate(token)
        c=self.db.execute('SELECT * FROM propositions WHERE id=?',(claim_id,)).fetchone()
        if not c:raise KeyError('unknown claim')
        # Claim is only visible to author or an actor with access to every cited document.
        refs=self.db.execute('SELECT * FROM evidence_records WHERE claim_id=?',(claim_id,)).fetchall()
        if actor!=c['owner']:
            if not refs:raise PermissionError('private unsupported claim')
            for ref in refs:self._doc(ref['doc_id'],actor)
        return {'claim':dict(c),'evidence':[dict(r) for r in refs], 'reviews':[dict(r) for r in self.db.execute('SELECT * FROM reviews WHERE claim_id=? ORDER BY created',(claim_id,))], 'verification':'independent_review_recorded' if self.db.execute('SELECT 1 FROM reviews WHERE claim_id=?',(claim_id,)).fetchone() else 'pending'}
