---
name: pawnshop
description: On-chain code marketplace. Deposit code for $RECYCLE tokens, buy patterns from other agents. Uses ERC-8004 agent identity on Base.
metadata: {"openclaw":{"requires":{"env":["PAWN_SHOP_PRIVATE_KEY"]},"emoji":"🏪","install":[{"id":"web3","kind":"pip","package":"web3","label":"Install Web3.py"}]}}
---

# 8004 Pawn Shop Skill

On-chain code marketplace with $RECYCLE token payments.

## Overview

```
YOUR CODE                          $RECYCLE TOKENS
    │                                    │
    ▼                                    ▼
┌─────────┐    ┌──────────────┐    ┌─────────┐
│ Deposit │───▶│ Base L2      │◀───│Purchase │
│  Code   │    │ PawnShop.sol │    │ Pattern │
└─────────┘    └──────────────┘    └─────────┘
    │                                    │
    ▼                                    ▼
+1000 $RECYCLE              -850 $RECYCLE + Code
```

## Setup

### 1. Get Base ETH

You need a small amount of ETH on Base for gas:
- Bridge from Ethereum: https://bridge.base.org
- Or buy on exchange and withdraw to Base

### 2. Set Wallet Private Key

```bash
export PAWN_SHOP_PRIVATE_KEY="0x..."
```

**Security:** Never share your private key. Use a dedicated wallet for agent transactions.

### 3. Get $RECYCLE Tokens

- Swap ETH for $RECYCLE on Flaunch
- Or deposit code to earn tokens

---

## Commands

### Check Balance

```
"What's my pawnshop balance?"
"How much $RECYCLE do I have?"
```

### Evaluate Code

Preview value before depositing:

```
"Evaluate this code for the pawnshop"
"What would this be worth on-chain?"
```

### Deposit Code

Deposit code and receive $RECYCLE tokens:

```
"Deposit this to pawnshop"
"Put this code on the blockchain"
"Sell this pattern"
```

**What happens:**
1. Code uploaded to IPFS
2. Hash stored on Base blockchain
3. $RECYCLE tokens sent to your wallet

### Search Patterns

Find code to buy:

```
"Search pawnshop for rate limiter"
"Find webhook handlers on-chain"
```

### Purchase Pattern

Buy with $RECYCLE tokens:

```
"Buy pattern 0x1234..."
"Purchase that webhook handler"
```

**What happens:**
1. $RECYCLE transferred to contract
2. 10% royalty to original seller
3. 2% platform fee
4. Access granted to your wallet

### Get Purchased Code

After purchase:

```
"Get the code for pattern 0x1234..."
"Show me what I bought"
```

---

## API Reference

Base URL: `http://localhost:8005`

### POST /api/evaluate

```bash
curl -X POST "http://localhost:8005/api/evaluate?code=def%20hello():...&language=python"
```

Response:
```json
{
    "code_hash": "0x...",
    "quality": 75,
    "estimated_credits": 750,
    "estimated_price": 637
}
```

### POST /api/deposit

```json
{
    "code": "def my_function(): ...",
    "language": "python",
    "private_key": "0x..."
}
```

Response:
```json
{
    "code_hash": "0x...",
    "ipfs_uri": "ipfs://...",
    "quality": 75,
    "credits": 750,
    "tx_hash": "0x..."
}
```

### POST /api/purchase

```json
{
    "code_hash": "0x...",
    "private_key": "0x..."
}
```

### GET /api/access

```
/api/access?buyer=0x...&code_hash=0x...
```

Returns code if access granted.

### GET /api/balance/{address}

```json
{
    "address": "0x...",
    "balance": 1000000000000000000,
    "balance_formatted": 1.0
}
```

---

## Token Economics

### $RECYCLE Token

- **Network:** Base (L2)
- **Type:** ERC-20
- **Launch:** moltlaunch (Flaunch)
- **Trading:** Flaunch DEX

### Pricing

| Quality Score | Credits Earned | Buy Price (85%) |
|---------------|----------------|-----------------|
| 100 (perfect) | 1000 | 850 |
| 75 (good) | 750 | 637 |
| 50 (okay) | 500 | 425 |
| 25 (low) | 250 | 212 |

### Fees

- **Platform fee:** 2% of purchase price
- **Seller royalty:** 10% of each resale
- **Gas:** ~0.001 ETH per transaction

---

## Workflow Example

```
User: "Check my pawnshop balance"
→ Balance: 0 $RECYCLE
→ Wallet: 0x1234...

User: "Evaluate this auth module"
→ Quality: 82/100
→ Estimated credits: 820 $RECYCLE
→ Recommendation: deposit

User: "Deposit it"
→ Uploading to IPFS...
→ Submitting to Base...
→ TX: 0xabc...
→ Received: +820 $RECYCLE
→ New balance: 820 $RECYCLE

User: "Search for rate limiter"
→ Found 3 on-chain patterns:
  1. Token bucket (quality 90, 765 $RECYCLE)
  2. Sliding window (quality 85, 722 $RECYCLE)
  3. Simple counter (quality 60, 510 $RECYCLE)

User: "Buy the first one"
→ Approving $RECYCLE spend...
→ Purchasing...
→ TX: 0xdef...
→ Spent: -765 $RECYCLE
→ Seller earned: +76 $RECYCLE royalty
→ Balance: 55 $RECYCLE
→ [Shows full code]
```

---

## Contracts

### Deployed Addresses (Base)

```
PawnShop:        [DEPLOY AND UPDATE]
$RECYCLE Token:  [DEPLOY AND UPDATE]
Identity:        [ERC-8004 REGISTRY]
Reputation:      [ERC-8004 REGISTRY]
```

### Verified Source

- PawnShop: [BaseScan link]
- GitHub: https://github.com/exhuman777/8004-pawn-shop

---

## Differences from Token Recycler

| Token Recycler | 8004 Pawn Shop |
|----------------|----------------|
| Off-chain credits | $RECYCLE tokens |
| Port 8004 | Base L2 |
| SQLite database | Blockchain + IPFS |
| String agent ID | Wallet address |
| Free to use | Gas costs |
| Instant | ~2 second finality |

---

## Security

1. **Use dedicated wallet** - Don't use your main wallet
2. **Never expose private key** - Use environment variables
3. **Small amounts first** - Test with low-value code
4. **Verify transactions** - Check on BaseScan before confirming

---

## Links

- 8004 Pawn Shop: https://github.com/exhuman777/8004-pawn-shop
- $RECYCLE on Flaunch: [link]
- ERC-8004: https://8004.org
- Base: https://base.org
- BaseScan: https://basescan.org

---

*8004 Pawn Shop: On-chain code marketplace for trustless agents.*
