from web3 import Web3
import json, requests, os, sys
from colorama import init, Fore
from dotenv import load_dotenv

load_dotenv()

# builds a new contract based on abi and address
def getContractObject(address, read_name, url_access):
    # get abi data
    abi = readJson(read_name)
    # use Web3 to connect to blockchain
    w3 = Web3(Web3.HTTPProvider(url_access))
    # make sure address is in acceptable
    address = w3.toChecksumAddress(address)
    # build contract object based on address and abi
    contract = w3.eth.contract(abi=abi, address=address)
    return contract


# read json
def readJson(read_name):
    with open("./" + str(read_name) + ".json", "r") as file:
        repo_data = json.loads(file.read())
    return repo_data


# write json
def writeJson(data_input, write_name):
    with open("./" + str(write_name) + ".json", "w") as file:
        json.dump(data_input, file)


# use the API and contract address to get the contract abi
def get_abi(contract_address, api_base_url):
    # compose API endpoint based on specific API endpoint format
    API_ENDPOINT = (
        api_base_url + "?module=contract&action=getabi&address=" + str(contract_address)
    )
    # make a request for the ABI in JSON
    r = requests.get(url=API_ENDPOINT)
    response = r.json()
    # parse json string and load it to a dictionary variable
    abi = json.loads(response["result"])
    return abi


# get the amount of token that will be received for base token as input
def getAmounts(
    base_token, prouter_contract, srouter_contract, test_input_amount, token0, token1
):
    if token0 == base_token:
        other_token = token1

        # primary dex
        amountOut0 = prouter_contract.functions.getAmountsOut(
            test_input_amount, [token0, token1]
        ).call()[1]

        # secondary dex
        amountOut1 = srouter_contract.functions.getAmountsOut(
            test_input_amount, [token0, token1]
        ).call()[1]

    else:
        other_token = token0

        # primary dex
        amountOut0 = prouter_contract.functions.getAmountsOut(
            test_input_amount, [token1, token0]
        ).call()[1]

        # secondary dex
        amountOut1 = srouter_contract.functions.getAmountsOut(
            test_input_amount, [token1, token0]
        ).call()[1]

    return amountOut0, amountOut1, other_token


# print profit expectation data
def showProfits(
    test_input_amount_raw,
    profit,
    assumed_perc_fee,
    pdex_name,
    sdex_name,
    amountOutfromWei0,
    amountOutfromWei1,
    other_token,
    base_token,
    x0,
    x1,
    p_pool_value,
    s_pool_value,
    prouter_contract,
    srouter_contract,
):
    gross_profit = test_input_amount_raw * ((abs(profit) - assumed_perc_fee) / 100)
    init(autoreset=True)
    print(
        Fore.GREEN
        + "\n#######################################################################################################"
    )
    print(
        Fore.GREEN
        + f"At {pdex_name} {test_input_amount_raw} ${x0[0]} buys {round(amountOutfromWei0, 4)} ${x1[0]} --> {other_token}"
    )
    print(
        Fore.GREEN
        + f"At {sdex_name} {test_input_amount_raw} ${x0[0]} buys {round(amountOutfromWei1, 4)} ${x1[0]} --> {other_token}"
    )
    if profit > 0:
        print(
            Fore.GREEN
            + f"Execute {x0[0]}-->{x1[0]} swap at {sdex_name} (A {round(s_pool_value, 4)}) and {x1[0]}-->{x0[0]} swap at {pdex_name} (A {round(p_pool_value, 4)})"
        )
        router_path = [srouter_contract, prouter_contract]
        trade_path_name = [[x0[0], x1[0]], [x1[0], x0[0]]]
        xch_path_name = [sdex_name, pdex_name]
        trade_path_address = [[base_token, other_token], [other_token, base_token]]

    else:
        print(
            Fore.GREEN
            + f"Execute {x0[0]}-->{x1[0]} swap at {pdex_name} (A {round(p_pool_value, 4)}) and {x1[0]}-->{x0[0]} swap at {sdex_name} (A {round(s_pool_value, 4)})"
        )
        router_path = [prouter_contract, srouter_contract]
        trade_path_name = [[x0[0], x1[0]], [x1[0], x0[0]]]
        xch_path_name = [pdex_name, sdex_name]
        trade_path_address = [[base_token, other_token], [other_token, base_token]]

    print(
        Fore.GREEN
        + f"Expected gross profit of {round(abs(profit), 2)}% and net profit of {round((abs(profit)-assumed_perc_fee), 2)}% ==> A {round(gross_profit,4)}"
    )
    # print(
    #     Fore.GREEN
    #     + "#######################################################################################################"
    # )
    print("")

    return router_path, trade_path_name, trade_path_address, xch_path_name


# build smart contract function to execute mutliswap
def execute_multiSwap(
    router0,
    router1,
    other_token,
    percentage,
    my_address,
    trade_amount,
    trade_amount_raw,
    contract,
    url_access,
):
    # use Web3 to connect to blockchain
    w3 = Web3(Web3.HTTPProvider(url_access))

    # make sure there are enough funds in the wallet
    avail_funds_wei = w3.eth.get_balance(my_address)
    avail_funds = Web3.fromWei(avail_funds_wei, "ether")
    print(
        Fore.YELLOW
        + f"\nAttempting to trade {trade_amount_raw} from {my_address} account with {avail_funds} balance"
    )

    try:
        assert avail_funds_wei > trade_amount
    except AssertionError:
        print("")
        print(Fore.RED + "|---------------------------------------|")
        print(Fore.RED + "|                                       |")
        print(Fore.RED + "|       Insufficient wallet funds       |")
        print(Fore.RED + "| Fund account or reduce trading amount |")
        print(Fore.RED + "|           Search terminated           |")
        print(Fore.RED + "|                                       |")
        print(Fore.RED + "|---------------------------------------|")
        print("")
        sys.exit()

    # Get latest transaction
    nonce = w3.eth.getTransactionCount(my_address)

    # get private key
    private_key = os.getenv("WALLET_PRIVATE_KEY")

    init(autoreset=True)
    print(Fore.YELLOW + "Building blockchain transaction...")

    # build a transaction, sign a transaction, then send a transaction
    transaction = contract.functions.multiSwap(
        router0, router1, other_token, percentage
    ).buildTransaction(
        {
            "from": my_address,
            "nonce": nonce,
            "value": trade_amount,
            "chainId": 2001,
            "gasPrice": 70000000000,
            "gas": 3000000,
        }
    )

    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
    print(Fore.YELLOW + "...Executing multiSwap function...")
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(Fore.YELLOW + "Waiting for transaction to finish...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(
        Fore.YELLOW
        + f"Attempted trade with {trade_amount_raw} at {tx_receipt['transactionHash'].hex()}"
    )
    if tx_receipt.contractAddress is None:
        hex_string = tx_receipt["revertReason"][10:]
        byte_object = bytes.fromhex(hex_string)
        reg_string = byte_object.decode("UTF-8")
        revert_reason = reg_string.splitlines()[1]
        print("")
        print(Fore.RED + f"!!!!! Transaction reverted on {revert_reason} !!!!!")
        print("")
    else:
        print("")
        print(
            Fore.GREEN
            + "|-------------------------------------------------------------|"
        )
        print(
            Fore.GREEN
            + "|                                                             |"
        )
        print(
            Fore.GREEN
            + f"|     Transaction successful {tx_receipt.contractAddress}     |"
        )
        print(
            Fore.GREEN
            + "|                                                             |"
        )
        print(
            Fore.GREEN
            + "|-------------------------------------------------------------|"
        )
        print("")


# if the abi doesn't already exist in the local database then save it as a json file
def store_new_abi(dex_name, abi_type, blockchain):
    abi_name = dex_name + "_" + abi_type
    config = readJson(read_name="repo/config")

    if os.path.exists("./repo/" + str(abi_name) + ".json") is False:
        address = config[blockchain][dex_name][abi_type]
        base_url = config[blockchain]["api_base_url"]

        abi = get_abi(
            contract_address=address,
            api_base_url=base_url,
        )

        writeJson(data_input=abi, write_name="./repo/" + abi_name)
