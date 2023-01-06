// SPDX-License-Identifier: GPL-3.0-or-later

pragma solidity ^0.8.0;

// uniswap callee
interface IUniswapV2Callee {
    function uniswapV2Call(
        address sender,
        uint256 amount0,
        uint256 amount1,
        bytes calldata data
    ) external;
}

// uniswap fork callee
interface ICallee {
    function Call(
        address sender,
        uint256 amount0,
        uint256 amount1,
        bytes calldata data
    ) external;
}

// Pair interface for flashloan
interface IPair {
    function totalSupply() external view returns (uint256);

    function balanceOf(address owner) external view returns (uint256);

    function allowance(
        address owner,
        address spender
    ) external view returns (uint256);

    function approve(address spender, uint256 value) external returns (bool);

    function transfer(address to, uint256 value) external returns (bool);

    function transferFrom(
        address from,
        address to,
        uint256 value
    ) external returns (bool);

    function token0() external view returns (address);

    function token1() external view returns (address);

    function swap(
        uint256 amount0Out,
        uint256 amount1Out,
        address to,
        bytes calldata data
    ) external;

    function skim(address to) external;

    function sync() external;

    function initialize(address, address) external;
}

// basic generic IER20 interface
interface IERC20 {
    function deposit() external payable;

    function transfer(address dst, uint256 wad) external returns (bool success);

    function balanceOf(address owner) external view returns (uint256 balance);

    function approve(address spender, uint256 amount) external returns (bool);
}

// basic generic router interface
interface IRouter {
    function getAmountsOut(
        uint256 amountIn,
        address[] memory path
    ) external view returns (uint256[] memory amounts);

    function getAmountsIn(
        uint256 amountOut,
        address[] calldata path
    ) external view returns (uint256[] memory amounts);

    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);

    function swapExactTokensForTokensSupportingFeeOnTransferTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external;
}

// uniswap clone factory interface
interface IFactory {
    event PairCreated(
        address indexed token0,
        address indexed token1,
        address pair,
        uint256
    );

    function getPair(
        address tokenA,
        address tokenB
    ) external view returns (address pair);

    function allPairs(uint256) external view returns (address pair);

    function allPairsLength() external view returns (uint256);

    function feeTo() external view returns (address);

    function feeToSetter() external view returns (address);

    function createPair(
        address tokenA,
        address tokenB
    ) external returns (address pair);
}

contract SimpleArbTrader {
    // address of wallet that deployed the contract
    address public owner;

    // the constructor is the first thing that happens when the contract is first instantiated
    // so this is the best time to allocate an owner of the contract - the person that deploys the contract is the owner
    constructor() {
        owner = msg.sender;
    }

    // this function is to fund contract
    function fund() public payable {}

    // see the balance in the contract
    function balance() public view returns (uint256) {
        return address(this).balance;
    }

    // restricted to only the owner of the smart contract
    modifier onlyOwner() {
        require(msg.sender == owner, "No Access");
        _;
    }

    // function to withdraw ERC20 funds from contract to the owner
    function withdrawERC20Funds(
        address _tokenContract
    ) public payable onlyOwner {
        // get the ERC20 contract
        IERC20 tokenContract = IERC20(_tokenContract);

        // get the amount of the token in the contract
        uint256 amount = tokenContract.balanceOf(address(this));

        // transfer the token from contract to owner
        tokenContract.transfer(msg.sender, amount);
    }

    // withdraw all base funds in the contract to the owner
    function withdrawBaseFunds() public payable onlyOwner {
        payable(msg.sender).transfer(address(this).balance);
    }

    // get the contract balance of a particular ERC20 token
    function getERC20Balance(
        address ERC20_address
    ) public view returns (uint256) {
        // get ERC20 contract
        IERC20 tokenContract = IERC20(ERC20_address);

        // get token balance
        uint256 ERC20_balance = tokenContract.balanceOf(address(this));

        return ERC20_balance;
    }

    // function to execute a swap on a UNISWAP style dex for any valid ERC20 trading pair - can only be called by contract
    function dexSwap(
        address _routerAddress,
        uint256 _amountIn,
        address[] calldata _path,
        uint256 _percentage
    ) private {
        // just to make sure the funds are actually available
        require(_amountIn > 0, "Insufficient funds in the contract");

        // get ERC20 token contract
        IERC20 tokenContract = IERC20(_path[0]);

        // approve the ERC20 token and amount that will be swapped via exchange router
        tokenContract.approve(_routerAddress, _amountIn);

        // get the router contract for exchange
        IRouter swapContract = IRouter(_routerAddress);

        // get a quote for the min amount out based on the amount in and the trade path in exchange0
        uint256[] memory _amountOutMin = swapContract.getAmountsOut(
            _amountIn,
            _path
        );

        uint256 getAmount = (_amountOutMin[1] / 100) * _percentage;

        // execute swap in exchange
        swapContract.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            _amountIn,
            getAmount,
            _path,
            address(this),
            block.timestamp
        );
    }

    // function to execute arbitrage opportunity - can only be called by owner
    function payMe(
        address _routerAddress0,
        address _routerAddress1,
        address[] calldata _path0,
        address[] calldata _path1,
        uint256 _percentage
    ) public payable onlyOwner {
        // swap all that is available
        uint256 _amountIn0 = getERC20Balance(_path0[0]);

        // execute first swap
        dexSwap(_routerAddress0, _amountIn0, _path0, _percentage);

        // get the amount of token recieved after swap available in the contract
        uint256 _amountIn1 = getERC20Balance(_path0[1]);

        // use that input amount to execute the next swap
        dexSwap(_routerAddress1, _amountIn1, _path1, _percentage);

        // ensure that the trade doesn't end with less out than in
        require(getERC20Balance(_path0[0]) >= _amountIn0, "False flag");
    }
}
