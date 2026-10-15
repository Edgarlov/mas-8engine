import json, sqlite3, hashlib
from pathlib import Path

CORES = {'ONTO-CORE','ENTE-CORE','EPI-CORE','META-CORE','LOG-CORE','SEM-CORE','AXIO-CORE','ETH-CORE','MIND-CORE','SCI-CORE','ENTIDAD CORE','PHIL-CORE','YO+'}
STATUS = {'RESPALDADO','INFERIDO','PROPUESTO','INCIERTO','DESCONOCIDO'}

def connect(path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(p,timeout=15)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS transactions (tx_id TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, payload TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS edges (id TEXT PRIMARY KEY, payload TEXT NOT NULL, transaction_id TEXT NOT NULL, FOREIGN KEY(transaction_id) REFERENCES transactions(tx_id))')
    db.execute('PRAGMA foreign_keys=ON')
    return db

def submit(path, envelope):
    for k in ('transaction_id','from_core','to_core','operation','payload','schema_version'):
        if k not in envelope: raise ValueError('missing:'+k)
    tx=envelope['transaction_id']
    if not isinstance(tx,str) or not tx.strip():raise ValueError('invalid transaction_id')
    if envelope['from_core'] not in CORES or envelope['to_core'] not in CORES:raise ValueError('unknown core')
    if envelope['schema_version']!='0.2.0':raise ValueError('unsupported schema')
    content=json.dumps(envelope,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    digest=hashlib.sha256(content.encode()).hexdigest()
    db=connect(path)
    try:
        db.execute('BEGIN IMMEDIATE')
        old=db.execute('SELECT payload_hash FROM transactions WHERE tx_id=?',(tx,)).fetchone()
        if old:
            if old[0]!=digest:raise ValueError('transaction_id collision')
            db.commit();return {'transaction_id':tx,'state':'ALREADY_RECORDED','digest':digest}
        db.execute('INSERT INTO transactions VALUES (?,?,?)',(tx,digest,content))
        db.commit();return {'transaction_id':tx,'state':'RECORDED','digest':digest}
    except:
        db.rollback();raise
    finally:db.close()

def get(path,tx_id):
    db=connect(path)
    try:
        row=db.execute('SELECT payload FROM transactions WHERE tx_id=?',(tx_id,)).fetchone()
        return json.loads(row[0]) if row else None
    finally:db.close()

def propose_edge(path,edge):
    required=('id','source_core','source_id','predicate','target_core','target_id','status','evidence','origin','transaction_id')
    for k in required:
        if k not in edge:raise ValueError('missing edge:'+k)
    if edge['source_core'] not in CORES or edge['target_core'] not in CORES:raise ValueError('unknown core')
    if edge['status'] not in STATUS: raise ValueError('unknown status')
    if edge.get('review_state')=='ACEPTADA':raise ValueError('accepted edges require independent external verification')
    db=connect(path)
    try:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM transactions WHERE tx_id=?',(edge['transaction_id'],)).fetchone():raise ValueError('unknown transaction')
        record=json.dumps(edge,sort_keys=True,ensure_ascii=False)
        prior=db.execute('SELECT payload FROM edges WHERE id=?',(edge['id'],)).fetchone()
        if prior and prior[0]!=record:raise ValueError('edge id collision')
        if not prior:db.execute('INSERT INTO edges VALUES(?,?,?)',(edge['id'],record,edge['transaction_id']))
        db.commit();return {'id':edge['id'],'state':'CANDIDATA'}
    except:
        db.rollback();raise
    finally:db.close()
