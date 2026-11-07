"""BIBLIOTHECA synthetic-only pilot. Not durable institutional memory."""
import hashlib, hmac, os, threading, time
from collections import defaultdict, deque
from fastapi import Request
from fastapi.responses import JSONResponse
from .integration import UniversityMemory
from .api import create_app
if os.environ.get("BIBLIOTHECA_PILOT_MODE")!="synthetic-only":
    raise RuntimeError("Requires synthetic-only pilot")
secret=os.environ.get("BIBLIOTHECA_PILOT_TOKEN","")
if len(secret)<40: raise RuntimeError("Requires pilot token >=40 characters")
root=os.environ.get("BIBLIOTHECA_HOME","/tmp/bibliotheca-pilot")
lib=UniversityMemory(root)
try:
    digest=hashlib.sha256(secret.encode()).hexdigest()
    with lib.db:
        lib.db.execute("INSERT OR IGNORE INTO principals(id,kind) VALUES('rectoria','human')")
        lib.db.execute("INSERT OR IGNORE INTO tokens(digest,principal,created,revoked) VALUES(?,?,?,NULL)",(digest,'rectoria',time.time()))
finally: lib.close()
app=create_app(root)
app.router.routes[:]=[r for r in app.router.routes if getattr(r,'path',None) not in ('/docs','/redoc','/openapi.json')]
requests_by_ip=defaultdict(deque)
lock=threading.Lock()
@app.middleware("http")
async def pilot_guard(request:Request,call_next):
    if request.url.path!="/health":
        size=request.headers.get("content-length")
        if size is None and request.method in ("POST","PUT","PATCH"):
            return JSONResponse({"detail":"content length required"},status_code=411)
        if size:
            try:n=int(size)
            except ValueError:return JSONResponse({"detail":"invalid size"},status_code=400)
            if n>65536:return JSONResponse({"detail":"payload too large"},status_code=413)
        auth=request.headers.get("authorization","")
        if not auth.startswith("Bearer ") or not hmac.compare_digest(auth[7:],secret):
            return JSONResponse({"detail":"unauthorized pilot"},status_code=401)
    ip=request.client.host if request.client else "unknown"
    now=time.monotonic()
    with lock:
        q=requests_by_ip[ip]
        while q and now-q[0]>60:q.popleft()
        if len(q)>=60:return JSONResponse({"detail":"rate limit"},status_code=429)
        q.append(now)
    return await call_next(request)
