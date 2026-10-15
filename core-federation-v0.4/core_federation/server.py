"""Independent FastMCP server; requires authenticated gateway before exposure."""
import os
from mcp.server.fastmcp import FastMCP
from .store import submit,get,propose_edge

DB=os.environ.get('CORE_FEDERATION_DB','/var/data/core_federation.sqlite3')
mcp=FastMCP('YO+ CORE Federation',stateless_http=True,json_response=True)
@mcp.tool()
def core_submit(envelope:dict)->dict:
    return submit(DB,envelope)
@mcp.tool()
def core_get(transaction_id:str)->dict:
    return {'result':get(DB,transaction_id)}
@mcp.tool()
def core_propose_edge(edge:dict)->dict:
    return propose_edge(DB,edge)
