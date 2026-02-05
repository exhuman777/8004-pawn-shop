#!/bin/bash
#
# Claim swap fees from moltlaunch
#
# Usage: ./scripts/claim-fees.sh
#

echo "=== Claiming \$RECYCLE Swap Fees ==="
echo ""

# Check balance first
echo "Checking available fees..."
npx moltlaunch balance --json

echo ""
read -p "Claim all fees? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Claim
echo ""
echo "Claiming..."
npx moltlaunch claim --json

echo ""
echo "=== Fees Claimed! ==="
