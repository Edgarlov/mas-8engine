"""BIBLIOTHECA 0.2: minimal deterministic, local-first library memory engine.
Not a distributed implementation; exposes auditable contracts for future agents.
"""
import hashlib, json, os, sqlite3, time, uuid
from pathlib import Path

ROLE_NAMES = ['Cartógrafo','Detector de ausencias','Archivista','Bibliotecario','Curador','Consolidador','Restaurador','Experimentador','Causalista','Inventor','Diseñador','Constructor','Orquestador','Asignador de roles','Planificador','Selector de estrategias','Gestor de incertidumbre','Historiador']

def _id(prefix): return f'{prefix}-{uuid.uuid4().hex[:16]}'
def _sha(b): return hashlib.sha256(b).hexdigest()

class Library:
    def __init__(self, root):
        self.root=Path(root).resolve(); self.root.mkdir(parents=True,exist_ok=True)
        self.objects=self.root/'objects';self.objects.mkdir(exist_ok=True)
        self.db=sqlite3.connect(self.root/'catalog.sqlite', timeout=15)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON');self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS docs(id TEXT PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL, owner TEXT NOT NULL, visibility TEXT NOT NULL CHECK(visibility IN ('private','public')), digest TEXT NOT NULL, created REAL NOT NULL, deleted REAL, license TEXT NOT NULL, source TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS permitted(doc_id TEXT REFERENCES docs(id), principal TEXT NOT NULL, PRIMARY KEY(doc_id,principal));
        CREATE TABLE IF NOT EXISTS claims(id TEXT PRIMARY KEY,doc_id TEXT NOT NULL REFERENCES docs(id), statement TEXT NOT NULL, epistemic TEXT NOT NULL CHECK(epistemic IN ('observed','verified','inferred','hypothesis','unknown')), created REAL NOT NULL, contradicted_by TEXT);
        CREATE TABLE IF NOT EXISTS gaps(id TEXT PRIMARY KEY, question TEXT NOT NULL, reason TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('open','resolved','rejected')), created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT NOT NULL, actor TEXT NOT NULL, ref TEXT, payload TEXT NOT NULL, created REAL NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_docs_title ON docs(title);
        ''');self.db.commit()
    def close(self):self.db.close()
    def _event(self,action,actor,ref,payload):self.db.execute('INSERT INTO events(action,actor,ref,payload,created) VALUES(?,?,?,?,?)',(action,actor,ref,json.dumps(payload,ensure_ascii=False,sort_keys=True),time.time()))
    def add(self,title,content,actor,source,kind='document',visibility='private',license='unspecified'):
        if not actor or not title or not source:raise ValueError('actor, title, source required')
        if visibility not in ('private','public'):raise ValueError('visibility invalid')
        data=content.encode('utf8') if isinstance(content,str) else bytes(content)
        h=_sha(data); target=self.objects/h
        if not target.exists():
            temp=self.objects/(h+'.'+uuid.uuid4().hex+'.tmp');temp.write_bytes(data)
            if _sha(temp.read_bytes())!=h:raise IOError('write verification failure')
            os.replace(temp,target)
        doc=_id('D')
        with self.db:
            self.db.execute('INSERT INTO docs VALUES(?,?,?,?,?,?,?,?,?,?)',(doc,title,kind,actor,visibility,h,time.time(),None,license,source))
            self.db.execute('INSERT INTO permitted VALUES(?,?)',(doc,actor))
            self._event('ingest',actor,doc,{'sha256':h,'source':source,'title':title})
        return {'id':doc,'sha256':h,'title':title}
    def _doc(self,doc_id,actor):
        d=self.db.execute('SELECT * FROM docs WHERE id=? AND deleted IS NULL',(doc_id,)).fetchone()
        if not d:raise KeyError('document absent or deleted')
        if d['visibility']!='public' and not self.db.execute('SELECT 1 FROM permitted WHERE doc_id=? AND principal=?',(doc_id,actor)).fetchone() and actor!=d['owner']:
            raise PermissionError('access denied')
        return d
    def read(self,doc_id,actor):
        d=self._doc(doc_id,actor); raw=(self.objects/d['digest']).read_bytes()
        if _sha(raw)!=d['digest']:raise IOError('hash mismatch; restore from independent backup')
        return {'id':doc_id,'title':d['title'],'source':d['source'],'sha256':d['digest'],'content':raw.decode('utf8')}
    def search(self,query,actor,limit=20):
        if not actor:raise ValueError('actor required')
        rows=self.db.execute('''SELECT id,title,kind,source FROM docs d WHERE deleted IS NULL AND (visibility='public' OR owner=? OR EXISTS(SELECT 1 FROM permitted p WHERE p.doc_id=d.id AND p.principal=?)) ORDER BY created DESC''',(actor,actor)).fetchall()
        terms=query.casefold().split();found=[]
        for row in rows:
            d=self.db.execute('SELECT digest FROM docs WHERE id=?',(row['id'],)).fetchone()
            raw=(self.objects/d['digest']).read_bytes()
            if _sha(raw)!=d['digest']:continue
            text=raw.decode('utf8',errors='replace').casefold();hay=(row['title']+' '+text).casefold()
            if all(t in hay for t in terms):found.append(dict(row))
            if len(found)>=limit:break
        return found
    def grant(self,doc_id,owner,principal):
        d=self._doc(doc_id,owner)
        if owner!=d['owner']:raise PermissionError('only owner may grant')
        if not principal:raise ValueError('principal required')
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO permitted VALUES(?,?)',(doc_id,principal))
            self._event('grant',owner,doc_id,{'principal':principal})
    def revoke(self,doc_id,owner,principal):
        d=self._doc(doc_id,owner)
        if owner!=d['owner']:raise PermissionError('only owner may revoke')
        with self.db:
            self.db.execute('DELETE FROM permitted WHERE doc_id=? AND principal=?',(doc_id,principal))
            self._event('revoke',owner,doc_id,{'principal':principal})
    def add_claim(self,doc_id,actor,statement,epistemic='hypothesis'):
        self._doc(doc_id,actor)
        if epistemic not in ('observed','verified','inferred','hypothesis','unknown'):raise ValueError('invalid epistemic state')
        cid=_id('C')
        with self.db:
            self.db.execute('INSERT INTO claims VALUES(?,?,?,?,?,?)',(cid,doc_id,statement,epistemic,time.time(),None))
            self._event('claim',actor,cid,{'doc_id':doc_id,'epistemic':epistemic})
        return cid
    def add_gap(self,question,reason,actor):
        if not all((question,reason,actor)):raise ValueError('missing gap fields')
        gid=_id('G')
        with self.db:
            self.db.execute('INSERT INTO gaps VALUES(?,?,?,?,?)',(gid,question,reason,'open',time.time()))
            self._event('gap',actor,gid,{'question':question,'reason':reason})
        return gid
    def gaps(self):return [dict(r) for r in self.db.execute('SELECT * FROM gaps ORDER BY created')]
    def delete(self,doc_id,actor):
        d=self._doc(doc_id,actor)
        if actor!=d['owner']:raise PermissionError('owner only')
        with self.db:
            self.db.execute('UPDATE docs SET deleted=? WHERE id=?',(time.time(),doc_id))
            self._event('tombstone',actor,doc_id,{'digest':d['digest'],'physical_erasure':'pending'})
        # Physical erasure requires policy for shared-content references, replicas and backups.
        return {'id':doc_id,'state':'tombstoned','physical_erasure':'not_implemented'}
    def verify(self):
        report=[]
        for d in self.db.execute('SELECT id,digest,deleted FROM docs'):
            p=self.objects/d['digest']
            report.append({'id':d['id'],'ok':p.exists() and _sha(p.read_bytes())==d['digest'],'deleted':d['deleted'] is not None})
        return report
    def history(self,actor,doc_id=None):
        # no leaking private doc event history
        if doc_id:self._doc(doc_id,actor)
        if not doc_id:raise ValueError('doc_id required for scoped history')
        return [dict(r) for r in self.db.execute('SELECT seq,action,actor,ref,payload,created FROM events WHERE ref=? ORDER BY seq',(doc_id,))]
    def export(self,actor):
        docs=self.db.execute('SELECT id FROM docs WHERE deleted IS NULL ORDER BY id').fetchall()
        result=[]
        for d in docs:
            try:result.append(self.read(d['id'],actor))
            except PermissionError:pass
        return {'format':'bibliotheca-export-v0.2','actor':actor,'documents':result}
