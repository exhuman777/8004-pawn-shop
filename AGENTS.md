# AGENTS.md

## Overview

On-chain code marketplace with ERC-8004 agent identity and $RECYCLE token payments. Evolution of Token Recycler to trustless on-chain.

## Stack

```
Contracts:   Solidity ^0.8.20 (Hardhat)
Backend:     Python FastAPI
Blockchain:  Base L2
Storage:     IPFS (code), on-chain (hashes)
```

## Commands

```bash
# Contracts
npm install
npx hardhat compile
npx hardhat test
npx hardhat run scripts/deploy.js --network base-sepolia

# API
cd api && pip install -r requirements.txt
uvicorn main:app --port 8005

# Token launch
npx moltlaunch --name "Recycle Token" --symbol "RECYCLE" ...
```

## Architecture

```
8004-pawn-shop/
  contracts/     # Solidity (PawnShop.sol, interfaces)
  api/           # FastAPI + Web3.py
  skill/         # Claude Code skill
  scripts/       # Deploy, token launch
  test/          # Hardhat tests
```

## Key Contracts

- **PawnShop.sol** - Deposit code hash, purchase access, royalties
- **IIdentityRegistry.sol** - ERC-8004 agent identity
- **IReputationRegistry.sol** - On-chain feedback

## Code Style

- Solidity: Use OpenZeppelin, natspec comments
- Python: `ruff format` + `ruff check`
- Tests: Hardhat + pytest

## Don't Touch

- Private keys, API secrets
- `.env` files
- Deployed contract addresses (unless upgrading)

## External Services

- Base L2 RPC
- IPFS (Pinata or similar)
- ERC-8004 registry (0x8004...)
- moltlaunch for token

## Related

- `~/Rufus/projects/token-recycler/` - Off-chain predecessor
