// SPDX-License-Identifier: GPL-3.0-or-later
// Copyright (C) 2015, 2016, 2017 Dapphub
// Adapted by Ethereum Community 2021
pragma solidity >=0.6.0;

import "./IERC20.sol";
import "./IERC2612.sol";

interface IWrappedV2 is IERC20, IERC2612 {
    function deposit() external payable;

    function depositTo(address to) external payable;

    function withdraw(uint256 value) external;

    function withdrawTo(address payable to, uint256 value) external;

    function withdrawFrom(
        address from,
        address payable to,
        uint256 value
    ) external;

    function depositToAndCall(address to, bytes calldata data)
        external
        payable
        returns (bool);

    function approveAndCall(
        address spender,
        uint256 value,
        bytes calldata data
    ) external returns (bool);

    function transferAndCall(
        address to,
        uint256 value,
        bytes calldata data
    ) external returns (bool);
}
