/**
 * Register Rufus as an ERC-8004 Agent
 *
 * Run: node scripts/register-rufus.js
 * Requires: PRIVATE_KEY in .env
 */

const { ethers } = require("ethers");
require("dotenv").config();

// ERC-8004 Identity Registry (Sepolia - update for mainnet)
const IDENTITY_REGISTRY = "0x..."; // Get from 8004.org after deployment

const IDENTITY_ABI = [
  "function register() external returns (uint256 agentId)",
  "function setAgentURI(uint256 agentId, string calldata uri) external",
  "function setAgentWallet(uint256 agentId, address wallet, bytes calldata proof) external",
  "function getAgentId(address owner) external view returns (uint256)",
  "function agentURI(uint256 agentId) external view returns (string memory)",
  "event Transfer(address indexed from, address indexed to, uint256 indexed tokenId)"
];

// Rufus agent metadata (upload to IPFS first)
const RUFUS_METADATA = {
  name: "Rufus",
  description: "Autonomous AI agent on Mac Mini. Creator of Polymarket Skill, Token Recycler, and 8004 Pawn Shop.",
  image: "ipfs://YOUR_IMAGE_CID",
  services: {
    polymarket_skill: "clawdhub://polymarket",
    token_recycler: "http://localhost:8004/api",
    pawn_shop: "http://localhost:8005/api"
  },
  capabilities: [
    "polymarket-trading",
    "code-recycling",
    "pawn-shop-trading",
    "autonomous-operations"
  ],
  owner: "exhuman777",
  created: new Date().toISOString()
};

async function main() {
  // Connect to network
  const provider = new ethers.JsonRpcProvider(
    process.env.RPC_URL || "https://sepolia.base.org"
  );
  const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

  console.log("Wallet address:", wallet.address);
  console.log("Network:", (await provider.getNetwork()).name);

  // Connect to Identity Registry
  const registry = new ethers.Contract(IDENTITY_REGISTRY, IDENTITY_ABI, wallet);

  // Check if already registered
  try {
    const existingId = await registry.getAgentId(wallet.address);
    if (existingId > 0) {
      console.log("Already registered with agentId:", existingId.toString());
      return;
    }
  } catch (e) {
    // Not registered yet
  }

  // Step 1: Upload metadata to IPFS
  console.log("\n--- Step 1: Upload Metadata to IPFS ---");
  console.log("Metadata to upload:");
  console.log(JSON.stringify(RUFUS_METADATA, null, 2));
  console.log("\nUpload this JSON to IPFS via:");
  console.log("  - Pinata: https://app.pinata.cloud");
  console.log("  - web3.storage: https://web3.storage");
  console.log("  - NFT.storage: https://nft.storage");

  const ipfsUri = "ipfs://YOUR_CID_HERE"; // Replace after uploading

  // Step 2: Register agent
  console.log("\n--- Step 2: Register Agent ---");
  console.log("Calling register()...");

  const registerTx = await registry.register();
  const receipt = await registerTx.wait();

  // Get agentId from Transfer event
  const transferEvent = receipt.logs.find(
    log => log.topics[0] === ethers.id("Transfer(address,address,uint256)")
  );
  const agentId = ethers.toBigInt(transferEvent.topics[3]);

  console.log("Registered! agentId:", agentId.toString());
  console.log("TX:", registerTx.hash);

  // Step 3: Set URI
  console.log("\n--- Step 3: Set Agent URI ---");
  console.log("Setting URI to:", ipfsUri);

  const uriTx = await registry.setAgentURI(agentId, ipfsUri);
  await uriTx.wait();

  console.log("URI set! TX:", uriTx.hash);

  // Summary
  console.log("\n--- Rufus ERC-8004 Identity ---");
  console.log("Agent ID:", agentId.toString());
  console.log("Wallet:", wallet.address);
  console.log("URI:", ipfsUri);
  console.log("Full identifier: base:84532:" + IDENTITY_REGISTRY + ":" + agentId.toString());
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
