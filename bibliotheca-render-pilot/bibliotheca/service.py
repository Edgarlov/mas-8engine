"""Authenticated service boundary for BIBLIOTHECA v0.3 (local-first, single-node).
This is not a Byzantine-fault-tolerant or multi-node distributed service.
"""
import hashlib, hmac, json, secrets, sqlite3, time, os, shutil
from pathlib import Path
from .core import Library, _sha

class MemoryService(Library):
    def __init__(self, root):
        super().__init__(root)
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS principals(id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('human','agent','service')), disabled INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS tokens(digest TEXT PRIMARY KEY, principal TEXT NOT NULL REFERENCES principals(id), created REAL NOT NULL, revoked REAL);
        CREATE TABLE IF NOT EXISTS links(id INTEGER PRIMARY KEY AUTOINCREMENT, src TEXT NOT NULL REFERENCES docs(id), dst TEXT NOT NULL REFERENCES docs(id), predicate TEXT NOT NULL, actor TEXT NOT NULL, created REAL NOT NULL, UNIQUE(src,dst,predicate));
        CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, role TEXT NOT NULL, requester TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('proposed','active','completed','failed','cancelled')), created REAL NOT NULL, result TEXT);
        CREATE TABLE IF NOT EXISTS audit_chain(seq INTEGER PRIMARY KEY AUTOINCREMENT,prev_hash TEXT NOT NULL,record_hash TEXT NOT NULL, action TEXT NOT NULL,actor TEXT NOT NULL,ref TEXT,payload TEXT NOT NULL,created REAL NOT NULL);
        CREATE VIRTUAL TABLE IF NOT EXISTS doc_fts USING fts5(doc_id UNINDEXED,title,body, tokenize='unicode61');
        ''')
        self.db.commit()

    def _event(self, action, actor, ref, payload):
        super()._event(action,actor,ref,payload)
        prev=self.db.execute('SELECT record_hash FROM audit_chain ORDER BY seq DESC LIMIT 1').fetchone()
        previous=prev[0] if prev else '0'*64
        stamp=time.time(); p=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':'))
        body=json.dumps([previous,action,actor,ref,p,stamp],ensure_ascii=False,separators=(',',':'))
        self.db.execute('INSERT INTO audit_chain(prev_hash,record_hash,action,actor,ref,payload,created) VALUES (?,?,?,?,?,?,?)',
            (previous,_sha(body.encode()),action,actor,ref,p,stamp))

    def bootstrap(self, principal='rectoria'):
        """Only for offline/console initialization; refuse if any principals exist."""
        if self.db.execute('SELECT 1 FROM principals LIMIT 1').fetchone():
            raise PermissionError('already initialized')
        return self._issue(principal,'human')

    def _issue(self, principal,kind):
        if not principal or kind not in ('human','agent','service'):raise ValueError('invalid principal')
        token=secrets.token_urlsafe(32)
        digest=_sha(token.encode())
        with self.db:
            self.db.execute('INSERT INTO principals(id,kind) VALUES (?,?)',(principal,kind))
            self.db.execute('INSERT INTO tokens(digest,principal,created) VALUES (?,?,?)',(digest,principal,time.time()))
            self._event('principal-created','system',principal,{'kind':kind})
        return {'principal':principal,'token':token}

    def authenticate(self,token):
        if not token:raise PermissionError('missing token')
        digest=_sha(token.encode());r=self.db.execute('SELECT p.id FROM tokens t JOIN principals p ON p.id=t.principal WHERE t.digest=? AND t.revoked IS NULL AND p.disabled=0',(digest,)).fetchone()
        if not r: raise PermissionError('invalid/revoked token')
        return r['id']

    def create_principal(self, admin_token, principal,kind='agent'):
        actor=self.authenticate(admin_token)
        self.require_admin(actor)
        return self._issue(principal,kind)

    def require_admin(self,actor):
        if actor!='rectoria':raise PermissionError('rectoria-only operation')

    def revoke_token(self,admin_token,target_token):
        actor=self.authenticate(admin_token);self.require_admin(actor)
        digest=_sha(target_token.encode())
        with self.db:
            count=self.db.execute('UPDATE tokens SET revoked=? WHERE digest=? AND principal<>?',(time.time(),digest,'rectoria')).rowcount
            self._event('token-revoked',actor,None,{'found':bool(count)})
        return bool(count)

    def deposit(self,token,title,content,source,**kwargs):
        actor=self.authenticate(token)
        result=self.add(title,content,actor,source,**kwargs)
        with self.db:
            self.db.execute('INSERT INTO doc_fts(doc_id,title,body) VALUES (?,?,?)',(result['id'],title,content if isinstance(content,str) else bytes(content).decode('utf8','replace')))
        return result

    def retrieve(self,token,doc_id):return self.read(doc_id,self.authenticate(token))

    def query(self,token,search,limit=20):
        actor=self.authenticate(token)
        if not search.strip():return []
        # FTS query is quoted as a phrase or AND of escaped tokens. No raw FTS syntax from clients.
        terms=[t.replace('"','""') for t in search.split()]
        fts=' AND '.join('"'+t+'"' for t in terms)
        lim=max(1,min(int(limit),100))
        rows=self.db.execute('''SELECT d.id,d.title,d.kind,d.source FROM doc_fts f JOIN docs d ON d.id=f.doc_id
          WHERE doc_fts MATCH ? AND d.deleted IS NULL AND
          (d.visibility='public' OR d.owner=? OR EXISTS(SELECT 1 FROM permitted p WHERE p.doc_id=d.id AND p.principal=?))
          ORDER BY bm25(doc_fts) LIMIT ?''',(fts,actor,actor,lim)).fetchall()
        return [dict(x) for x in rows]

    def relate(self,token,source_id,target_id,predicate):
        actor=self.authenticate(token)
        self._doc(source_id,actor);self._doc(target_id,actor)
        if predicate not in {'references','supports','contradicts','derived_from','replaces','depends_on'}:raise ValueError('predicate not supported')
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO links(src,dst,predicate,actor,created) VALUES (?,?,?,?,?)',(source_id,target_id,predicate,actor,time.time()))
            self._event('relate',actor,source_id,{'target':target_id,'predicate':predicate})
        return {'source':source_id,'target':target_id,'predicate':predicate}

    def relations(self,token,doc_id):
        actor=self.authenticate(token);self._doc(doc_id,actor)
        # Filter target too, to avoid leaking private object identities.
        result=[]
        for row in self.db.execute('SELECT src,dst,predicate FROM links WHERE src=? OR dst=?',(doc_id,doc_id)):
            try:self._doc(row['src'],actor);self._doc(row['dst'],actor)
            except (KeyError,PermissionError):continue
            result.append(dict(row))
        return result

    def claim(self,token,doc_id,statement,state='hypothesis'):
        actor=self.authenticate(token)
        return self.add_claim(doc_id,actor,statement,state)

    def gap(self,token,question,reason):
        return self.add_gap(question,reason,self.authenticate(token))

    def check(self,token):
        actor=self.authenticate(token)
        out=[]
        for r in self.verify():
            try:self._doc(r['id'],actor)
            except (PermissionError,KeyError):continue
            out.append(r)
        return out

    def grant_access(self,token,doc_id,principal):
        actor=self.authenticate(token)
        if not self.db.execute('SELECT 1 FROM principals WHERE id=? AND disabled=0',(principal,)).fetchone():raise KeyError('unknown principal')
        return self.grant(doc_id,actor,principal)

    def revoke_access(self,token,doc_id,principal):return self.revoke(doc_id,self.authenticate(token),principal)

    def retire(self,token,doc_id):return self.delete(doc_id,self.authenticate(token))

    def erase(self,token,doc_id):
        """Delete document's physical object if unreferenced; no backup erasure claim."""
        actor=self.authenticate(token)
        d=self.db.execute('SELECT * FROM docs WHERE id=?',(doc_id,)).fetchone()
        if not d:raise KeyError('document missing')
        if actor!=d['owner']:raise PermissionError('owner only')
        digest=d['digest']
        with self.db:
            self.db.execute('DELETE FROM links WHERE src=? OR dst=?',(doc_id,doc_id))
            self.db.execute('DELETE FROM claims WHERE doc_id=?',(doc_id,))
            self.db.execute('DELETE FROM permitted WHERE doc_id=?',(doc_id,))
            self.db.execute('DELETE FROM doc_fts WHERE doc_id=?',(doc_id,))
            self.db.execute('DELETE FROM docs WHERE id=?',(doc_id,))
            self._event('erasure',actor,doc_id,{'content_sha256':digest,'backup_erasure':'not_guaranteed'})
        n=self.db.execute('SELECT count(*) FROM docs WHERE digest=?',(digest,)).fetchone()[0]
        if n==0:(self.objects/digest).unlink(missing_ok=True)
        return {'id':doc_id,'active_object_exists':(self.objects/digest).exists(),'backup_erasure':'not_guaranteed'}

    def audit(self,token):
        actor=self.authenticate(token);self.require_admin(actor)
        previous='0'*64;count=0
        for r in self.db.execute('SELECT * FROM audit_chain ORDER BY seq'):
            body=json.dumps([previous,r['action'],r['actor'],r['ref'],r['payload'],r['created']],ensure_ascii=False,separators=(',',':'))
            if r['prev_hash']!=previous or r['record_hash']!=_sha(body.encode()):return {'valid':False,'broken_seq':r['seq']}
            previous=r['record_hash'];count+=1
        return {'valid':True,'events':count,'head':previous,'note':'Local hash chain detects accidental edits, not privileged rewriting of chain.'}

    def backup(self, token, destination):
        actor=self.authenticate(token);self.require_admin(actor)
        dst=Path(destination).resolve()
        if dst==self.root or self.root in dst.parents:raise ValueError('backup must be outside source root')
        if dst.exists():raise FileExistsError('destination exists')
        dst.mkdir(parents=True)
        try:
            with sqlite3.connect(dst/'catalog.sqlite') as backupdb:
                self.db.backup(backupdb)
            shutil.copytree(self.objects,dst/'objects')
            manifest={p.name:_sha(p.read_bytes()) for p in (dst/'objects').iterdir() if p.is_file()}
            (dst/'manifest.json').write_text(json.dumps(manifest,sort_keys=True),encoding='utf8')
            return {'destination':str(dst),'objects':len(manifest),'db_bytes':(dst/'catalog.sqlite').stat().st_size}
        except Exception:
            shutil.rmtree(dst);raise

    @staticmethod
    def verify_backup(directory):
        d=Path(directory);manifest=json.loads((d/'manifest.json').read_text('utf8'))
        bad=[name for name,digest in manifest.items() if not (d/'objects'/name).is_file() or _sha((d/'objects'/name).read_bytes())!=digest]
        with sqlite3.connect(d/'catalog.sqlite') as db:
            intact=db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            required={r[0] for r in db.execute('SELECT DISTINCT digest FROM docs')}
        return {'valid':not bad and intact and required.issubset(manifest.keys()),'bad_objects':bad,'sqlite_ok':intact,'missing_objects':list(required-manifest.keys())}

    def create_task(self,token,role,description):
        from .core import ROLE_NAMES, _id
        actor=self.authenticate(token)
        if role not in ROLE_NAMES:raise ValueError('unknown role')
        if not description.strip():raise ValueError('empty task')
        tid=_id('TASK')
        with self.db:
            self.db.execute('INSERT INTO tasks(id,role,requester,status,created,result) VALUES (?,?,?,?,?,?)',(tid,role,actor,'proposed',time.time(),description))
            self._event('task-proposed',actor,tid,{'role':role})
        return {'task_id':tid,'role':role,'status':'proposed','note':'No autonomous worker launched'}

    def list_tasks(self,token):
        actor=self.authenticate(token)
        rows=self.db.execute('SELECT id,role,status,created,result FROM tasks WHERE requester=? ORDER BY created DESC',(actor,)).fetchall()
        return [dict(r) for r in rows]
