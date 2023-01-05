import json

# this is the compiler for solidity
from solcx import compile_standard, install_solc

# read solidity smart contract to a variable
with open("./ArbTraderV1.sol", "r") as file:
    simple_arb_trader = file.read()

# install the version of solidity being used
install_solc("0.8.7")

# compile solidity code
compile_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"ArbTraderV1.sol": {"content": simple_arb_trader}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.8.7",
    allow_paths=[
        "/Users/amadeus/Desktop/GitHub Projects/ArbMilkomeda",
        "/Users/amadeus/Desktop/GitHub Projects/ArbMilkomeda/interfaces",
    ],
)

# dump base code to json file
with open("compiled_code.json", "w") as file:
    json.dump(compile_sol, file)
