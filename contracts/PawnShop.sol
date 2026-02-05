// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title PawnShop
 * @notice On-chain code marketplace with ERC-8004 agent identity
 * @dev Agents deposit code hashes, receive $RECYCLE tokens
 */
contract PawnShop is Ownable, ReentrancyGuard {
    // =============================================================
    //                           STORAGE
    // =============================================================

    IERC20 public immutable recycleToken;
    address public identityRegistry;
    address public reputationRegistry;
    address public treasury;

    uint256 public platformFeeBps = 200; // 2%
    uint256 public royaltyBps = 1000;    // 10%
    uint256 public minQuality = 10;
    uint256 public maxQuality = 100;

    struct Pattern {
        bytes32 codeHash;
        string ipfsUri;
        address seller;
        uint256 price;
        uint256 quality;
        uint256 deposited;
        uint256 timesSold;
        bool active;
    }

    // codeHash => Pattern
    mapping(bytes32 => Pattern) public patterns;

    // buyer => codeHash => hasAccess
    mapping(address => mapping(bytes32 => bool)) public access;

    // seller => total earnings
    mapping(address => uint256) public earnings;

    // Total patterns
    uint256 public totalPatterns;
    uint256 public totalSales;

    // =============================================================
    //                           EVENTS
    // =============================================================

    event PatternDeposited(
        bytes32 indexed codeHash,
        address indexed seller,
        string ipfsUri,
        uint256 price,
        uint256 quality
    );

    event PatternPurchased(
        bytes32 indexed codeHash,
        address indexed buyer,
        address indexed seller,
        uint256 price,
        uint256 royalty
    );

    event PatternDeactivated(bytes32 indexed codeHash, address indexed seller);

    event FeesUpdated(uint256 platformFeeBps, uint256 royaltyBps);

    // =============================================================
    //                         CONSTRUCTOR
    // =============================================================

    constructor(
        address _recycleToken,
        address _treasury
    ) Ownable(msg.sender) {
        recycleToken = IERC20(_recycleToken);
        treasury = _treasury;
    }

    // =============================================================
    //                        CORE FUNCTIONS
    // =============================================================

    /**
     * @notice Deposit code pattern and receive $RECYCLE tokens
     * @param codeHash Keccak256 hash of the code
     * @param ipfsUri IPFS URI where full code is stored
     * @param quality Quality score 10-100
     * @return credits Amount of $RECYCLE tokens received
     */
    function deposit(
        bytes32 codeHash,
        string calldata ipfsUri,
        uint256 quality
    ) external nonReentrant returns (uint256 credits) {
        require(codeHash != bytes32(0), "Invalid code hash");
        require(bytes(ipfsUri).length > 0, "Invalid IPFS URI");
        require(quality >= minQuality && quality <= maxQuality, "Quality out of range");
        require(!patterns[codeHash].active, "Pattern already exists");

        // Calculate credits based on quality
        credits = _calculateCredits(quality);

        // Calculate price (85% of credits)
        uint256 price = (credits * 85) / 100;

        // Store pattern
        patterns[codeHash] = Pattern({
            codeHash: codeHash,
            ipfsUri: ipfsUri,
            seller: msg.sender,
            price: price,
            quality: quality,
            deposited: block.timestamp,
            timesSold: 0,
            active: true
        });

        totalPatterns++;

        // Transfer $RECYCLE to seller
        require(
            recycleToken.transfer(msg.sender, credits),
            "Token transfer failed"
        );

        emit PatternDeposited(codeHash, msg.sender, ipfsUri, price, quality);
    }

    /**
     * @notice Purchase access to a code pattern
     * @param codeHash Hash of the pattern to purchase
     */
    function purchase(bytes32 codeHash) external nonReentrant {
        Pattern storage p = patterns[codeHash];
        require(p.active, "Pattern not found");
        require(!access[msg.sender][codeHash], "Already purchased");
        require(msg.sender != p.seller, "Cannot buy own pattern");

        uint256 price = p.price;

        // Transfer payment from buyer
        require(
            recycleToken.transferFrom(msg.sender, address(this), price),
            "Payment failed"
        );

        // Calculate fees
        uint256 platformFee = (price * platformFeeBps) / 10000;
        uint256 royalty = (price * royaltyBps) / 10000;
        uint256 remaining = price - platformFee - royalty;

        // Transfer platform fee to treasury
        if (platformFee > 0) {
            recycleToken.transfer(treasury, platformFee);
        }

        // Transfer royalty to seller
        if (royalty > 0) {
            recycleToken.transfer(p.seller, royalty);
            earnings[p.seller] += royalty;
        }

        // Remaining stays in contract (or burn)

        // Grant access
        access[msg.sender][codeHash] = true;
        p.timesSold++;
        totalSales++;

        emit PatternPurchased(codeHash, msg.sender, p.seller, price, royalty);
    }

    /**
     * @notice Check if buyer has access to pattern
     */
    function hasAccess(address buyer, bytes32 codeHash) external view returns (bool) {
        return access[buyer][codeHash];
    }

    /**
     * @notice Get pattern details
     */
    function getPattern(bytes32 codeHash) external view returns (
        string memory ipfsUri,
        address seller,
        uint256 price,
        uint256 quality,
        uint256 timesSold,
        bool active
    ) {
        Pattern memory p = patterns[codeHash];
        return (p.ipfsUri, p.seller, p.price, p.quality, p.timesSold, p.active);
    }

    /**
     * @notice Deactivate own pattern (seller only)
     */
    function deactivate(bytes32 codeHash) external {
        Pattern storage p = patterns[codeHash];
        require(p.seller == msg.sender, "Not seller");
        require(p.active, "Already inactive");

        p.active = false;
        emit PatternDeactivated(codeHash, msg.sender);
    }

    // =============================================================
    //                        INTERNAL
    // =============================================================

    function _calculateCredits(uint256 quality) internal pure returns (uint256) {
        // quality 10-100 => credits 100-1000
        return quality * 10;
    }

    // =============================================================
    //                         ADMIN
    // =============================================================

    function setFees(uint256 _platformFeeBps, uint256 _royaltyBps) external onlyOwner {
        require(_platformFeeBps <= 500, "Platform fee too high"); // max 5%
        require(_royaltyBps <= 2000, "Royalty too high");          // max 20%

        platformFeeBps = _platformFeeBps;
        royaltyBps = _royaltyBps;

        emit FeesUpdated(_platformFeeBps, _royaltyBps);
    }

    function setTreasury(address _treasury) external onlyOwner {
        treasury = _treasury;
    }

    function setRegistries(address _identity, address _reputation) external onlyOwner {
        identityRegistry = _identity;
        reputationRegistry = _reputation;
    }

    function withdrawStuck(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner(), amount);
    }

    // =============================================================
    //                          VIEWS
    // =============================================================

    function stats() external view returns (
        uint256 _totalPatterns,
        uint256 _totalSales,
        uint256 _platformFeeBps,
        uint256 _royaltyBps
    ) {
        return (totalPatterns, totalSales, platformFeeBps, royaltyBps);
    }
}
