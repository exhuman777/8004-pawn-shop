#!/bin/bash
#
# Launch $RECYCLE token via moltlaunch
#
# Usage: ./scripts/launch-token.sh
#
# Prerequisites:
# - npm installed
# - Wallet with Base ETH (for gas)
# - Logo image in project root
#

set -e

echo "=== Launching \$RECYCLE Token ==="
echo ""

# Check for logo
if [ ! -f "logo.png" ]; then
    echo "Warning: logo.png not found. Using placeholder."
    echo "Create a 500x500 PNG logo for better branding."
fi

# Token details
NAME="Recycle Token"
SYMBOL="RECYCLE"
DESCRIPTION="Utility token for the 8004 Pawn Shop - on-chain code marketplace for AI agents. Deposit code, earn \$RECYCLE. Buy patterns, spend \$RECYCLE."
WEBSITE="https://moltbook.com/m/8004-pawn-shop"

echo "Token Details:"
echo "  Name: $NAME"
echo "  Symbol: $SYMBOL"
echo "  Website: $WEBSITE"
echo ""

# Confirm
read -p "Launch token? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Launch
echo ""
echo "Launching..."
echo ""

if [ -f "logo.png" ]; then
    npx moltlaunch \
        --name "$NAME" \
        --symbol "$SYMBOL" \
        --description "$DESCRIPTION" \
        --image ./logo.png \
        --website "$WEBSITE" \
        --json
else
    npx moltlaunch \
        --name "$NAME" \
        --symbol "$SYMBOL" \
        --description "$DESCRIPTION" \
        --website "$WEBSITE" \
        --json
fi

echo ""
echo "=== Token Launched! ==="
echo ""
echo "Next steps:"
echo "1. Save the token address"
echo "2. Update .env with RECYCLE_TOKEN_ADDRESS"
echo "3. Add liquidity on Flaunch"
echo "4. Update PawnShop contract with token address"
echo "5. Announce on Twitter, Moltbook, Telegram"
