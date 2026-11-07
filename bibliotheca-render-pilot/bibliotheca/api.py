"""Authenticated HTTP interface. Bind to loopback by default; use TLS reverse proxy for any remote access."""
import os
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from .integration import UniversityMemory

class Deposit(BaseModel):
    title:str; content:str;source:str;visibility:str='private';license:str='unspecified'
class Relation(BaseModel):
    source_id:str;target_id:str;predicate:str
class Claim(BaseModel):
    doc_id:str;statement:str;state:str='hypothesis'
class Gap(BaseModel):
    question:str;reason:str
class Task(BaseModel):
    role:str;description:str
class Unit(BaseModel):
    unit_id:str;kind:str;title:str;parent:str|None=None
class Affiliation(BaseModel):
    unit_id:str;principal:str;role:str='member'
class EpistemicClaim(BaseModel):
    statement:str;epistemic:str='hypothesis';uncertainty:float|None=None;uncertainty_basis:str|None=None
class EvidenceRef(BaseModel):
    claim_id:str;doc_id:str;locator:str;method:str;relationship:str='supports'
class IndependentReview(BaseModel):
    claim_id:str;finding:str;reason:str
class Principal(BaseModel):
    name:str;kind:str='agent'
class Permission(BaseModel):
    principal:str


def create_app(root=None):
    if not root:root=os.environ.get('BIBLIOTHECA_HOME')
    if not root:raise RuntimeError('BIBLIOTHECA_HOME required')
    app=FastAPI(title='BIBLIOTHECA University Memory API',version='0.4.0')
    def library():
        lib=UniversityMemory(root)
        try:yield lib
        finally:lib.close()
    def auth(authorization:str|None=Header(default=None)):
        if not authorization or not authorization.startswith('Bearer '):raise HTTPException(401,'missing bearer token')
        return authorization[7:]
    def guard(fn,*args,**kwargs):
        try:return fn(*args,**kwargs)
        except PermissionError:raise HTTPException(403,'forbidden')
        except KeyError:raise HTTPException(404,'not found')
        except ValueError as e:raise HTTPException(422,str(e))
        except (IOError,FileNotFoundError):raise HTTPException(409,'object integrity or availability failure')

    @app.get('/health')
    def health():return {'status':'up','scope':'single-node'}
    @app.post('/v1/principals')
    def principal(req:Principal, token=Depends(auth),lib=Depends(library)):
        return guard(lib.create_principal,token,req.name,req.kind)
    @app.post('/v1/memory/deposit')
    def deposit(req:Deposit,token=Depends(auth),lib=Depends(library)):
        return guard(lib.deposit,token,req.title,req.content,req.source,visibility=req.visibility,license=req.license)
    @app.get('/v1/memory/{doc_id}')
    def retrieve(doc_id:str,token=Depends(auth),lib=Depends(library)):
        return guard(lib.retrieve,token,doc_id)
    @app.get('/v1/search')
    def search(q:str,limit:int=20,token=Depends(auth),lib=Depends(library)):
        return guard(lib.query,token,q,limit)
    @app.post('/v1/relations')
    def relate(req:Relation,token=Depends(auth),lib=Depends(library)):
        return guard(lib.relate,token,req.source_id,req.target_id,req.predicate)
    @app.get('/v1/relations/{doc_id}')
    def relations(doc_id:str,token=Depends(auth),lib=Depends(library)):
        return guard(lib.relations,token,doc_id)
    @app.post('/v1/claims')
    def claim(req:Claim,token=Depends(auth),lib=Depends(library)):
        return {'id':guard(lib.claim,token,req.doc_id,req.statement,req.state)}
    @app.post('/v1/gaps')
    def gap(req:Gap,token=Depends(auth),lib=Depends(library)):
        return {'id':guard(lib.gap,token,req.question,req.reason)}
    @app.post('/v1/access/{doc_id}/grant')
    def grant(doc_id:str,req:Permission,token=Depends(auth),lib=Depends(library)):
        guard(lib.grant_access,token,doc_id,req.principal);return {'ok':True}
    @app.post('/v1/access/{doc_id}/revoke')
    def revoke(doc_id:str,req:Permission,token=Depends(auth),lib=Depends(library)):
        guard(lib.revoke_access,token,doc_id,req.principal);return {'ok':True}
    @app.delete('/v1/memory/{doc_id}')
    def delete(doc_id:str,token=Depends(auth),lib=Depends(library)):
        return guard(lib.erase,token,doc_id)
    @app.post('/v1/tasks')
    def task(req:Task,token=Depends(auth),lib=Depends(library)):
        return guard(lib.create_task,token,req.role,req.description)
    @app.get('/v1/tasks')
    def tasks(token=Depends(auth),lib=Depends(library)):
        return guard(lib.list_tasks,token)
    @app.post('/v1/university/units')
    def register_unit(req:Unit,token=Depends(auth),lib=Depends(library)):
        return guard(lib.register_unit,token,req.unit_id,req.kind,req.title,req.parent)
    @app.post('/v1/university/affiliations')
    def affiliate(req:Affiliation,token=Depends(auth),lib=Depends(library)):
        return guard(lib.affiliate,token,req.unit_id,req.principal,req.role)
    @app.get('/v1/university/units')
    def units(token=Depends(auth),lib=Depends(library)):
        return guard(lib.units_for,token)
    @app.post('/v1/epistemic/claims')
    def assert_claim(req:EpistemicClaim,token=Depends(auth),lib=Depends(library)):
        return guard(lib.assert_claim,token,req.statement,req.epistemic,req.uncertainty,req.uncertainty_basis)
    @app.post('/v1/epistemic/evidence')
    def cite(req:EvidenceRef,token=Depends(auth),lib=Depends(library)):
        return guard(lib.cite,token,req.claim_id,req.doc_id,req.locator,req.method,req.relationship)
    @app.post('/v1/epistemic/reviews')
    def review(req:IndependentReview,token=Depends(auth),lib=Depends(library)):
        return guard(lib.review_claim,token,req.claim_id,req.finding,req.reason)
    @app.get('/v1/epistemic/dossiers/{claim_id}')
    def dossier(claim_id:str,token=Depends(auth),lib=Depends(library)):
        return guard(lib.dossier,token,claim_id)
    @app.get('/v1/audit')
    def audit(token=Depends(auth),lib=Depends(library)):
        return guard(lib.audit,token)
    return app
