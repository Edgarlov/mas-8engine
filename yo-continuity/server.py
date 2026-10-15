import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from auth import BearerAuth
from controller import update, current, open_db

DB=Path(os.environ.get('YO_DB_PATH','/var/data/yo_continuity.sqlite3'))
mcp=FastMCP('YO+ Continuity Controller',host='0.0.0.0',port=int(os.environ.get('PORT','10000')),stateless_http=True,json_response=True)

@mcp.tool()
def continuity_update(project:str,repetition:float,stalled:float,lost_context:float,outcome:float|None=None)->dict:
    DB.parent.mkdir(parents=True,exist_ok=True)
    return update(DB,project,dict(repetition=repetition,stalled=stalled,lost_context=lost_context,outcome=outcome))

@mcp.tool()
def continuity_status(project:str)->dict:
    DB.parent.mkdir(parents=True,exist_ok=True)
    con=open_db(DB)
    try:return current(con,project)
    finally:con.close()

app=BearerAuth(mcp.streamable_http_app())
