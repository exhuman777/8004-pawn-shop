#!/usr/bin/env python3
"""
8004 Pawn Shop API
==================
On-chain code marketplace with ERC-8004 agent identity.
Connects to PawnShop contract on Base.

Run: uvicorn main:app --port 8005
"""

import os
import json
import hashlib
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3
from eth_account import Account
import requests

# =============================================================================
# CONFIG
# =============================================================================

# Network
RPC_URL = os.environ.get("BASE_RPC_URL", "https://base.llamarpc.com")
CHAIN_ID = 8453  # Base mainnet

# Contracts (deploy and update these)
PAWN_SHOP_ADDRESS = os.environ.get("PAWN_SHOP_ADDRESS", "")
RECYCLE_TOKEN_ADDRESS = os.environ.get("RECYCLE_TOKEN_ADDRESS", "")
IDENTITY_REGISTRY_ADDRESS = os.environ.get("IDENTITY_REGISTRY_ADDRESS", "")

# IPFS
IPFS_GATEWAY = "https://gateway.pinata.cloud/ipfs/"
PINATA_API_KEY = os.environ.get("PINATA_API_KEY", "")
PINATA_SECRET = os.environ.get("PINATA_SECRET", "")

# ABIs (simplified - load full ABIs in production)
PAWN_SHOP_ABI = [
    {
        "inputs": [
            {"name": "codeHash", "type": "bytes32"},
            {"name": "ipfsUri", "type": "string"},
            {"name": "quality", "type": "uint256"}
        ],
        "name": "deposit",
        "outputs": [{"name": "credits", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "codeHash", "type": "bytes32"}],
        "name": "purchase",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "buyer", "type": "address"},
            {"name": "codeHash", "type": "bytes32"}
        ],
        "name": "hasAccess",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "codeHash", "type": "bytes32"}],
        "name": "getPattern",
        "outputs": [
            {"name": "ipfsUri", "type": "string"},
            {"name": "seller", "type": "address"},
            {"name": "price", "type": "uint256"},
            {"name": "quality", "type": "uint256"},
            {"name": "timesSold", "type": "uint256"},
            {"name": "active", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "stats",
        "outputs": [
            {"name": "_totalPatterns", "type": "uint256"},
            {"name": "_totalSales", "type": "uint256"},
            {"name": "_platformFeeBps", "type": "uint256"},
            {"name": "_royaltyBps", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# =============================================================================
# WEB3 CLIENT
# =============================================================================

w3 = Web3(Web3.HTTPProvider(RPC_URL))

def get_pawn_shop():
    if not PAWN_SHOP_ADDRESS:
        raise HTTPException(500, "PawnShop contract not configured")
    return w3.eth.contract(address=PAWN_SHOP_ADDRESS, abi=PAWN_SHOP_ABI)

def get_recycle_token():
    if not RECYCLE_TOKEN_ADDRESS:
        raise HTTPException(500, "RECYCLE token not configured")
    return w3.eth.contract(address=RECYCLE_TOKEN_ADDRESS, abi=ERC20_ABI)

def hash_code(code: str) -> bytes:
    """Generate keccak256 hash of code."""
    return w3.keccak(text=code)

def sign_and_send(tx: dict, private_key: str) -> str:
    """Sign and send transaction."""
    account = Account.from_key(private_key)
    tx['from'] = account.address
    tx['nonce'] = w3.eth.get_transaction_count(account.address)
    tx['gas'] = 300000
    tx['gasPrice'] = w3.eth.gas_price

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return tx_hash.hex()

# =============================================================================
# IPFS CLIENT
# =============================================================================

def upload_to_ipfs(content: str) -> str:
    """Upload content to IPFS via Pinata."""
    if not PINATA_API_KEY:
        # Fallback: return hash as mock URI
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"ipfs://mock/{content_hash}"

    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET
    }
    data = {
        "pinataContent": {"code": content},
        "pinataMetadata": {"name": "pawnshop-pattern"}
    }

    r = requests.post(url, json=data, headers=headers)
    if r.status_code == 200:
        ipfs_hash = r.json()["IpfsHash"]
        return f"ipfs://{ipfs_hash}"
    else:
        raise HTTPException(500, f"IPFS upload failed: {r.text}")

def fetch_from_ipfs(uri: str) -> str:
    """Fetch content from IPFS."""
    if uri.startswith("ipfs://mock/"):
        raise HTTPException(404, "Mock IPFS content not available")

    ipfs_hash = uri.replace("ipfs://", "")
    url = f"{IPFS_GATEWAY}{ipfs_hash}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json().get("code", "")
    else:
        raise HTTPException(404, "IPFS content not found")

# =============================================================================
# QUALITY SCORING (same as token-recycler)
# =============================================================================

def estimate_quality(code: str) -> int:
    """Score code quality 10-100."""
    scores = []

    # Length check
    lines = code.count('\n') + 1
    if 10 <= lines <= 500:
        scores.append(100)
    elif lines < 10:
        scores.append(50)
    else:
        scores.append(70)

    # Has structure
    if "def " in code or "class " in code or "function " in code:
        scores.append(100)
    else:
        scores.append(60)

    # Has comments/docs
    if "#" in code or "//" in code or '"""' in code:
        scores.append(90)
    else:
        scores.append(70)

    # Line lengths
    long_lines = sum(1 for line in code.split('\n') if len(line) > 120)
    if long_lines == 0:
        scores.append(100)
    elif long_lines < 5:
        scores.append(80)
    else:
        scores.append(50)

    # Average and scale to 10-100
    avg = sum(scores) / len(scores)
    return max(10, min(100, int(avg)))

# =============================================================================
# MODELS
# =============================================================================

class DepositRequest(BaseModel):
    code: str
    language: str = "python"
    private_key: Optional[str] = None  # For signing tx

class PurchaseRequest(BaseModel):
    code_hash: str
    private_key: str

class QueryRequest(BaseModel):
    query: str
    language: Optional[str] = None
    max_results: int = 10

# =============================================================================
# API
# =============================================================================

app = FastAPI(
    title="8004 Pawn Shop",
    description="On-chain code marketplace with ERC-8004 agent identity",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "8004 Pawn Shop",
        "version": "1.0.0",
        "chain": "Base",
        "chain_id": CHAIN_ID,
        "contracts": {
            "pawn_shop": PAWN_SHOP_ADDRESS or "not deployed",
            "recycle_token": RECYCLE_TOKEN_ADDRESS or "not deployed",
            "identity_registry": IDENTITY_REGISTRY_ADDRESS or "not deployed"
        },
        "endpoints": [
            "/api/deposit",
            "/api/purchase",
            "/api/access",
            "/api/pattern",
            "/api/balance",
            "/api/stats",
            "/api/evaluate"
        ]
    }

@app.post("/api/evaluate")
async def evaluate(code: str, language: str = "python"):
    """Preview what code would be worth (no blockchain interaction)."""
    quality = estimate_quality(code)
    credits = quality * 10  # Same formula as contract
    price = int(credits * 0.85)
    code_hash = hash_code(code).hex()

    return {
        "code_hash": code_hash,
        "quality": quality,
        "estimated_credits": credits,
        "estimated_price": price,
        "recommendation": "deposit" if quality >= 50 else "improve_quality"
    }

@app.post("/api/deposit")
async def deposit(req: DepositRequest):
    """Deposit code pattern on-chain."""
    if len(req.code) < 50:
        raise HTTPException(400, "Code too short (min 50 chars)")

    # Calculate quality
    quality = estimate_quality(req.code)

    # Hash code
    code_hash = hash_code(req.code)

    # Upload to IPFS
    ipfs_uri = upload_to_ipfs(req.code)

    # If no private key, return unsigned tx data
    if not req.private_key:
        return {
            "code_hash": code_hash.hex(),
            "ipfs_uri": ipfs_uri,
            "quality": quality,
            "estimated_credits": quality * 10,
            "tx_data": {
                "to": PAWN_SHOP_ADDRESS,
                "function": "deposit",
                "args": [code_hash.hex(), ipfs_uri, quality]
            },
            "message": "Sign and submit this transaction to deposit"
        }

    # Sign and send transaction
    pawn_shop = get_pawn_shop()
    tx = pawn_shop.functions.deposit(
        code_hash,
        ipfs_uri,
        quality
    ).build_transaction({
        'chainId': CHAIN_ID,
    })

    tx_hash = sign_and_send(tx, req.private_key)

    return {
        "code_hash": code_hash.hex(),
        "ipfs_uri": ipfs_uri,
        "quality": quality,
        "credits": quality * 10,
        "tx_hash": tx_hash,
        "message": f"Deposited! +{quality * 10} $RECYCLE"
    }

@app.post("/api/purchase")
async def purchase(req: PurchaseRequest):
    """Purchase access to a pattern."""
    code_hash = bytes.fromhex(req.code_hash.replace("0x", ""))

    pawn_shop = get_pawn_shop()

    # Get pattern info first
    pattern = pawn_shop.functions.getPattern(code_hash).call()
    if not pattern[5]:  # active
        raise HTTPException(404, "Pattern not found or inactive")

    price = pattern[2]

    # Build and send transaction
    tx = pawn_shop.functions.purchase(code_hash).build_transaction({
        'chainId': CHAIN_ID,
    })

    tx_hash = sign_and_send(tx, req.private_key)

    return {
        "code_hash": req.code_hash,
        "price": price,
        "tx_hash": tx_hash,
        "message": f"Purchased! -{price} $RECYCLE"
    }

@app.get("/api/access")
async def check_access(buyer: str, code_hash: str):
    """Check if buyer has access, return code if yes."""
    code_hash_bytes = bytes.fromhex(code_hash.replace("0x", ""))

    pawn_shop = get_pawn_shop()
    has_access = pawn_shop.functions.hasAccess(buyer, code_hash_bytes).call()

    if not has_access:
        return {"has_access": False, "code": None}

    # Get IPFS URI and fetch code
    pattern = pawn_shop.functions.getPattern(code_hash_bytes).call()
    ipfs_uri = pattern[0]

    try:
        code = fetch_from_ipfs(ipfs_uri)
    except:
        code = None

    return {
        "has_access": True,
        "ipfs_uri": ipfs_uri,
        "code": code
    }

@app.get("/api/pattern/{code_hash}")
async def get_pattern(code_hash: str):
    """Get pattern details."""
    code_hash_bytes = bytes.fromhex(code_hash.replace("0x", ""))

    pawn_shop = get_pawn_shop()
    pattern = pawn_shop.functions.getPattern(code_hash_bytes).call()

    return {
        "code_hash": code_hash,
        "ipfs_uri": pattern[0],
        "seller": pattern[1],
        "price": pattern[2],
        "quality": pattern[3],
        "times_sold": pattern[4],
        "active": pattern[5]
    }

@app.get("/api/balance/{address}")
async def get_balance(address: str):
    """Get $RECYCLE balance."""
    token = get_recycle_token()
    balance = token.functions.balanceOf(address).call()

    return {
        "address": address,
        "balance": balance,
        "balance_formatted": balance / 1e18
    }

@app.get("/api/stats")
async def get_stats():
    """Get marketplace statistics."""
    pawn_shop = get_pawn_shop()
    stats = pawn_shop.functions.stats().call()

    return {
        "total_patterns": stats[0],
        "total_sales": stats[1],
        "platform_fee_bps": stats[2],
        "royalty_bps": stats[3],
        "chain": "Base",
        "chain_id": CHAIN_ID
    }

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
