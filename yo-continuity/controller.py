import json, math, sqlite3
from datetime import datetime, timezone
from pathlib import Path

def check(x):
    if not isinstance(x,(int,float)) or not math.isfinite(x) or not 0<=x<=1: raise ValueError('signals must be in [0,1]')

def open_db(db):
    con=sqlite3.connect(str(db),timeout=15)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('CREATE TABLE IF NOT EXISTS events(project TEXT NOT NULL, seq INTEGER NOT NULL, ts TEXT NOT NULL, payload TEXT NOT NULL, result TEXT NOT NULL, PRIMARY KEY(project,seq))')
    return con

def current(con,project):
    row=con.execute('SELECT result FROM events WHERE project=? ORDER BY seq DESC LIMIT 1',(project,)).fetchone()
    return json.loads(row[0]) if row else {'step':0,'risk':0.0,'mode':'explore'}

def update(db,project,event):
    if not isinstance(project,str) or not project.strip(): raise ValueError('project required')
    for k in ('repetition','stalled','lost_context'):check(event[k])
    if event.get('outcome') is not None:check(event['outcome'])
    u=max(0.,min(1.,.3*event['repetition']+.4*event['stalled']+.3*event['lost_context']-.2*(event.get('outcome') or 0.)))
    con=open_db(db)
    try:
        con.execute('BEGIN IMMEDIATE')
        p=current(con,project);r=.7*p['risk']+.3*u;m=p['mode']
        if m=='explore' and r>=.65:m='recover'
        elif m=='recover' and r<=.30:m='explore'
        state={'step':p['step']+1,'risk':r,'instant_risk':u,'mode':m}
        con.execute('INSERT INTO events VALUES(?,?,?,?,?)',(project,state['step'],datetime.now(timezone.utc).isoformat(),json.dumps(event),json.dumps(state)))
        con.commit();return state
    except Exception:
        con.rollback();raise
    finally:con.close()
