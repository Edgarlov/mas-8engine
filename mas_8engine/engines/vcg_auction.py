"""
MAS-8ENGINE │ vcg_auction.py
Mercado Microeconómico de Subastas Vickrey-Clarke-Groves (VCG) de Cómputo y Recursos VRAM.
"""
from __future__ import annotations

from typing import Dict, List, Tuple
from pydantic import BaseModel


class AgentBid(BaseModel):
    agent_id: str
    bid_value: float


class VCGAuctionResult(BaseModel):
    winner_agent_id: str
    vcg_payment: float
    social_welfare: float


class VCGAuctionEngine:
    """Motor de Subasta VCG para asignación eficiente de VRAM y CPU entre subagentes."""

    @classmethod
    def run_auction(cls, bids: List[AgentBid]) -> VCGAuctionResult:
        if not bids:
            return VCGAuctionResult(winner_agent_id="NONE", vcg_payment=0.0, social_welfare=0.0)

        # Ordenar pujas por valor descendente (Vickrey Auction rule)
        sorted_bids = sorted(bids, key=lambda x: x.bid_value, reverse=True)
        winner = sorted_bids[0]
        
        # El ganador paga el valor de la segunda puja más alta (Vickrey Pricing)
        vcg_payment = sorted_bids[1].bid_value if len(sorted_bids) > 1 else 0.0
        welfare = sum(b.bid_value for b in bids)

        return VCGAuctionResult(
            winner_agent_id=winner.agent_id,
            vcg_payment=round(vcg_payment, 2),
            social_welfare=round(welfare, 2)
        )
