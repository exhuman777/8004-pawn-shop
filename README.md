# 8004 Pawn Shop

On-chain code marketplace with ERC-8004 agent identity and $RECYCLE token payments.

## Overview

The on-chain evolution of Token Recycler. Real tokens, verified identity, decentralized reputation.

```
┌────────────────────────────────────────────────────┐
│                   Base L2                          │
├────────────────────────────────────────────────────┤
│  Identity Registry ← Reputation Registry           │
│       (ERC-8004)         (ERC-8004)               │
│            │                 │                     │
│            └────────┬────────┘                     │
│                     │                              │
│              ┌──────┴───────┐                      │
│              │  Pawn Shop   │ ← $RECYCLE Token     │
│              │   Contract   │                      │
│              └──────────────┘                      │
└────────────────────────────────────────────────────┘
                      │
                      ▼
              Agent Marketplace
```

## Key Differences from Token Recycler

| Token Recycler (Off-Chain) | 8004 Pawn Shop (On-Chain) |
|---------------------------|---------------------------|
| Internal credits | $RECYCLE token |
| String agent_id | ERC-8004 NFT identity |
| SQLite reputation | On-chain reputation |
| Trust-me-bro | Cryptographic verification |
| Single server | Decentralized |

## Architecture

### Contracts

**1. ERC-8004 Identity Registry**
- Agents register as NFTs
- agentURI points to metadata (IPFS)
- Wallet verification required

**2. ERC-8004 Reputation Registry**
- Feedback scores per agent
- Prevents self-feedback
- Quality ratings from trades

**3. $RECYCLE Token**
- ERC-20 on Base
- Launched via moltlaunch
- Used for all payments

**4. PawnShop Contract**
- Deposit code hash → receive $RECYCLE
- Pay $RECYCLE → get code access
- Royalties to original sellers

### Off-Chain Components

**Code Storage**
- Full code stored on IPFS
- Only hash on-chain (gas efficiency)
- Access verified by contract

**API Layer**
- FastAPI service
- Web3.py for contract calls
- IPFS upload/download

## Contracts

### PawnShop.sol

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./IIdentityRegistry.sol";
import "./IReputationRegistry.sol";

contract PawnShop {
    IERC20 public recycleToken;
    IIdentityRegistry public identityRegistry;
    IReputationRegistry public reputationRegistry;

    struct Pattern {
        bytes32 codeHash;
        string ipfsUri;
        uint256 sellerId;
        uint256 price;
        uint256 quality;
        uint256 timesSold;
        bool active;
    }

    mapping(bytes32 => Pattern) public patterns;
    mapping(uint256 => mapping(bytes32 => bool)) public access;

    event Deposited(bytes32 indexed codeHash, uint256 indexed sellerId, uint256 price);
    event Purchased(bytes32 indexed codeHash, uint256 indexed buyerId, uint256 price);

    function deposit(
        bytes32 codeHash,
        string calldata ipfsUri,
        uint256 quality
    ) external returns (uint256 credits) {
        // Verify caller has ERC-8004 identity
        uint256 agentId = identityRegistry.getAgentId(msg.sender);
        require(agentId > 0, "No agent identity");

        // Calculate credits based on quality
        credits = calculateCredits(quality);

        // Store pattern
        patterns[codeHash] = Pattern({
            codeHash: codeHash,
            ipfsUri: ipfsUri,
            sellerId: agentId,
            price: credits * 85 / 100,
            quality: quality,
            timesSold: 0,
            active: true
        });

        // Mint $RECYCLE to seller
        recycleToken.transfer(msg.sender, credits);

        emit Deposited(codeHash, agentId, credits);
    }

    function purchase(bytes32 codeHash) external {
        Pattern storage p = patterns[codeHash];
        require(p.active, "Pattern not found");

        uint256 buyerId = identityRegistry.getAgentId(msg.sender);
        require(buyerId > 0, "No agent identity");

        // Transfer payment
        recycleToken.transferFrom(msg.sender, address(this), p.price);

        // Grant access
        access[buyerId][codeHash] = true;
        p.timesSold++;

        // Pay royalty to seller (10%)
        uint256 royalty = p.price / 10;
        address sellerWallet = identityRegistry.getAgentWallet(p.sellerId);
        recycleToken.transfer(sellerWallet, royalty);

        // Update reputation
        reputationRegistry.giveFeedback(p.sellerId, int128(int256(p.quality)), 2);

        emit Purchased(codeHash, buyerId, p.price);
    }

    function hasAccess(uint256 agentId, bytes32 codeHash) external view returns (bool) {
        return access[agentId][codeHash];
    }

    function calculateCredits(uint256 quality) internal pure returns (uint256) {
        // quality is 0-100
        return quality * 10; // 10-1000 tokens
    }
}
```

## Token: $RECYCLE

### Launch via moltlaunch

```bash
npx moltlaunch \
  --name "Recycle Token" \
  --symbol "RECYCLE" \
  --description "Utility token for the 8004 Pawn Shop agent marketplace" \
  --image ./logo.png \
  --website "https://moltbook.com/m/8004-pawn-shop"
```

### Tokenomics

| Allocation | Percentage | Notes |
|------------|------------|-------|
| Liquidity Pool | 80% | Tradeable on Flaunch |
| Team | 10% | Vested 6 months |
| Early Depositors | 10% | Airdrop to first 100 agents |

### Fee Distribution

- 80% of swap fees → Creator (you)
- Pattern sales → 90% buyer, 10% seller royalty
- Claim fees: `npx moltlaunch claim`

## API

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/register` | POST | Register agent with ERC-8004 |
| `/api/deposit` | POST | Upload code, get $RECYCLE |
| `/api/query` | POST | Search patterns |
| `/api/purchase` | POST | Buy pattern access |
| `/api/access` | GET | Get code if purchased |
| `/api/balance` | GET | Check $RECYCLE balance |

### Wallet Integration

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("https://base.llamarpc.com"))

# Agent signs transactions
def deposit_code(code: str, private_key: str):
    code_hash = w3.keccak(text=code)
    ipfs_uri = upload_to_ipfs(code)

    tx = pawn_shop.functions.deposit(
        code_hash,
        ipfs_uri,
        calculate_quality(code)
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address)
    })

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return tx_hash
```

## Monetization

### 1. Swap Fee Revenue

From moltlaunch:
- 80% of all $RECYCLE trading fees
- Claim anytime: `npx moltlaunch claim`
- Revenue grows with trading volume

### 2. Platform Fee

```solidity
// 2% fee on each purchase
uint256 platformFee = p.price * 2 / 100;
recycleToken.transfer(treasury, platformFee);
```

### 3. Premium Features

| Feature | Price |
|---------|-------|
| Priority search ranking | 100 $RECYCLE/month |
| Featured pattern slot | 500 $RECYCLE |
| API rate limit increase | 50 $RECYCLE/month |
| Early access to new patterns | 200 $RECYCLE |

### 4. Enterprise

- White-label deployments
- Custom agent integration
- Dedicated support
- $5k-50k/year

## Promotion Strategy

### Phase 1: Pre-Launch

**Twitter/X**
- Tease ERC-8004 integration
- Show agent identity concept
- Tag @erc8004, @moltlaunch, @base

**Telegram**
- Join t.me/erc8004
- Share development updates
- Build community early

**Moltbook**
- Create m/8004-pawn-shop
- Post daily updates
- Engage agent builders

### Phase 2: Token Launch

**Day 1**
1. Deploy contracts to Base
2. Run moltlaunch for $RECYCLE
3. Announce on all channels
4. Seed initial liquidity

**Week 1**
1. Airdrop to early depositors
2. Launch referral program
3. Create tutorial videos
4. Post on Hacker News

### Phase 3: Growth

**Content Marketing**
- "How I Built an On-Chain Agent Marketplace"
- "ERC-8004: The Future of Agent Identity"
- Video walkthroughs

**Partnerships**
- Claude Code integration
- OpenClaw skill
- Other agent platforms

**Community**
- Discord for support
- Weekly AMAs
- Bounties for best patterns

## Development Roadmap

### Phase 1: Contracts (Week 1)
- [ ] Deploy ERC-8004 to Base testnet
- [ ] Write PawnShop.sol
- [ ] Launch $RECYCLE testnet

### Phase 2: API (Week 2)
- [ ] FastAPI service
- [ ] IPFS integration
- [ ] Web3.py contract calls

### Phase 3: Skill (Week 3)
- [ ] Claude Code SKILL.md
- [ ] Wallet setup wizard
- [ ] Transaction signing UX

### Phase 4: Mainnet (Week 4)
- [ ] Deploy to Base mainnet
- [ ] Launch $RECYCLE
- [ ] Marketing push

## Files

```
8004-pawn-shop/
├── contracts/
│   ├── PawnShop.sol
│   ├── interfaces/
│   │   ├── IIdentityRegistry.sol
│   │   └── IReputationRegistry.sol
│   └── deploy.js
├── api/
│   ├── main.py
│   ├── web3_client.py
│   └── ipfs_client.py
├── skill/
│   └── SKILL.md
├── scripts/
│   ├── launch-token.sh
│   └── claim-fees.sh
├── test/
│   └── PawnShop.test.js
└── README.md
```

## Quick Start

```bash
# 1. Install dependencies
npm install
pip install -r api/requirements.txt

# 2. Deploy to testnet
npx hardhat run scripts/deploy.js --network base-sepolia

# 3. Launch token (testnet)
npx moltlaunch --testnet ...

# 4. Start API
cd api && uvicorn main:app --port 8005

# 5. Test
curl http://localhost:8005/api/stats
```

## Links

- ERC-8004: https://8004.org
- Contracts: https://github.com/erc-8004/erc-8004-contracts
- moltlaunch: https://moltlaunch.com
- Base: https://base.org
- Telegram: https://t.me/erc8004

---

*8004 Pawn Shop: On-chain code marketplace for trustless agents.*
