// SPDX-License-Identifier: GPL-3.0-or-later

pragma solidity >=0.8.0;

import "./UniswapV2Library.sol";
import "interfaces/IPair.sol";
import "interfaces/IERC20.sol";
import "interfaces/IRouter.sol";
import "interfaces/IFactory.sol";
import "interfaces/IWrappedV2.sol";

contract SimpleArbTrader {
    // address of wallet that deployed the contract
    address public owner;
    address public _wbaseCoin = 0xAE83571000aF4499798d1e3b0fA0070EB3A3E3F9;
    address[] flashDEX;

    IWrappedV2 wbaseCoin = IWrappedV2(_wbaseCoin);

    // the constructor is the first thing that happens when the contract is first instantiated
    // so this is the best time to allocate an owner of the contract - the person that deploys the contract is the owner
    constructor() {
        owner = msg.sender;
    }

    // restricted to only the owner of the smart contract
    modifier onlyOwner() {
        require(msg.sender == owner, "No Access");
        _;
    }

    // get wallet balance
    function walletBalance() public view returns (uint256) {
        return msg.sender.balance;
    }

    // withdraw all base funds in the contract to the owner
    function withdrawBase() public onlyOwner {
        (bool sent, ) = payable(msg.sender).call{value: address(this).balance}(
            new bytes(0)
        );

        // if failed throw error on blockchain
        require(sent, "Failed to milk the contract!");
    }

    // function to withdraw ERC20 funds from contract to the owner
    function harvestERC20(address _tokenContract) public onlyOwner {
        // get the ERC20 contract
        IERC20 tokenContract = IERC20(_tokenContract);

        // get the amount of the token in the contract
        uint256 amount = tokenContract.balanceOf(address(this));

        // transfer the token from contract to owner
        bool sent = tokenContract.transfer(msg.sender, amount);

        // if failed throw error on blockchain
        require(sent, "Failed to harvest the contract!");
    }

    // see the balance of the base coin (eg ETH) in the contract
    function base_balance() public view returns (uint256) {
        return address(this).balance;
    }

    // get the contract balance of a particular ERC20 token
    function ERC20Balance(address ERC20_address) public view returns (uint256) {
        // get ERC20 contract
        IERC20 tokenContract = IERC20(ERC20_address);

        // get the amount of token received after swap
        uint256 ERC20_balance = tokenContract.balanceOf(address(this));

        return ERC20_balance;
    }

    // function to execute a swap on a UNISWAP style dex for any valid ERC20 trading pair - can only be called by contract
    function dexSwap(
        address _routerAddress,
        uint256 _amountIn,
        address[] memory _path,
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
            block.timestamp + 1800
        );
    }

    // function to execute arbitrage opportunity - can only be called by owner
    // this function is designed to use the contract as a funnel for the funds from the owner
    // to wrap the token, execute the swap, unwrap and harvest the the balance
    // but only if the balance is greater than the input amount plus a tolerance
    function multiSwap(
        address _routerAddress0,
        address _routerAddress1,
        address _other_token,
        uint256 _percentage
    ) public payable onlyOwner {
        // automatically wrap incoming funds
        wbaseCoin.deposit{value: msg.value}();

        // amount to swap
        uint256 _amountIn0 = msg.value;

        address[] memory _path0 = new address[](2);
        _path0[0] = _wbaseCoin;
        _path0[1] = _other_token;

        address[] memory _path1 = new address[](2);
        _path1[0] = _other_token;
        _path1[1] = _wbaseCoin;

        // execute first swap
        dexSwap(_routerAddress0, _amountIn0, _path0, _percentage);

        // get ERC20 token contract
        IERC20 tokenContract = IERC20(_path0[1]);

        // get the amount of token received after swap
        uint256 _amountIn1 = tokenContract.balanceOf(address(this));

        // use that input amount to execute the next swap
        dexSwap(_routerAddress1, _amountIn1, _path1, _percentage);

        // get the amount of token received after swap
        uint256 _result = wbaseCoin.balanceOf(address(this));

        // send wrapped funds to msg.sender
        harvestERC20(_wbaseCoin);

        // ensure that the trade doesn't end with less out than in
        // uint256 _tolerance = 200000000000000000; // assuming a gas fee as high as 0.2
        require(_result > _amountIn0, "False flag");
    }

    // needs to accept ETH from any V1 exchange and WETH.
    receive() external payable {}

    fallback() external payable {}
}
