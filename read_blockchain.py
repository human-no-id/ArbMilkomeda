from modules.modules import (
    readJson,
    getContractObject,
    getAmounts,
    showProfits,
    execute_multiSwap,
)
from web3 import Web3, exceptions
from tqdm import tqdm
import time, sys, simpleaudio
from colorama import init, Fore


def scan_blockchain(
    all_pairs,
    config,
    blockchain,
    useful_tokens,
    base_token,
    test_input_amount,
    test_input_amount_raw,
    pdex_name,
    sdex_name,
    perc_profit_threshold,
    pfactory_contract,
    sfactory_contract,
    prouter_contract,
    srouter_contract,
    arb_contract,
    pool_size_threshold,
    assumed_perc_fee,
    trade_amount_raw,
    trade_amount,
    total_slippage,
    my_address,
):

    # critical_error = False

    # loop through pairs and get pair contract object
    init(autoreset=True)
    for pair_no in tqdm(
        range(all_pairs),
        Fore.YELLOW + f"Scanning {pdex_name} and {sdex_name}:",
        leave=False,
    ):
        p_pair_address = pfactory_contract.functions.allPairs(pair_no).call()
        p_pair_contract = getContractObject(
            address=p_pair_address,
            read_name="repo/uniswapV2_pool",
            url_access=config[blockchain]["url_access"],
        )

        # get token addresses
        token0 = p_pair_contract.functions.token0().call()
        token1 = p_pair_contract.functions.token1().call()

        # check that the token match those considered useful
        if token0 in useful_tokens and token1 in useful_tokens:

            # check also that the pair include WADA
            if token0 == base_token or token1 == base_token:
                # get the contract for the pair at the secondary dex
                s_pair_address = sfactory_contract.functions.getPair(
                    token0, token1
                ).call()

                s_pair_contract = getContractObject(
                    address=s_pair_address,
                    read_name="repo/uniswapV2_pool",
                    url_access=config[blockchain]["url_access"],
                )

                # get reserves for both primary and secondary dex
                p_reserves = p_pair_contract.functions.getReserves().call()

                try:
                    s_reserves = s_pair_contract.functions.getReserves().call()

                    # estimate pool size
                    if s_pair_contract.functions.token0().call() == base_token:
                        s_pool_value = s_reserves[0] * 2
                    else:
                        s_pool_value = s_reserves[1] * 2

                    if token0 == base_token:
                        p_pool_value = p_reserves[0] * 2
                    else:
                        p_pool_value = p_reserves[1] * 2

                    # convert to human readable WADA value
                    p_pool_value = Web3.fromWei(p_pool_value, "ether")
                    s_pool_value = Web3.fromWei(s_pool_value, "ether")

                    # only consider pair pools larger than a specified threshold
                    if (
                        p_pool_value >= pool_size_threshold
                        and s_pool_value >= pool_size_threshold
                    ):
                        # get the amount of token that will be received for base token as input
                        amountOut0, amountOut1, other_token = getAmounts(
                            base_token,
                            prouter_contract,
                            srouter_contract,
                            test_input_amount,
                            token0,
                            token1,
                        )

                        # find the name of the base and other tokens
                        x0 = [
                            y
                            for y in config[blockchain]["tokens"]
                            if config[blockchain]["tokens"][y] == base_token
                        ]
                        x1 = [
                            y
                            for y in config[blockchain]["tokens"]
                            if config[blockchain]["tokens"][y] == other_token
                        ]

                        # get value of other token and potential profit
                        amountOutfromWei0 = amountOut0 / (
                            10 ** config[blockchain]["token_decimals"][x1[0]]
                        )
                        amountOutfromWei1 = amountOut1 / (
                            10 ** config[blockchain]["token_decimals"][x1[0]]
                        )
                        profit = (
                            (amountOutfromWei1 - amountOutfromWei0) / amountOutfromWei0
                        ) * 100

                        # make trade
                        if abs(profit) > perc_profit_threshold:
                            # display results and identify trade path
                            (
                                router_path,
                                trade_path_name,
                                trade_path_address,
                                xch_path_name,
                            ) = showProfits(
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
                            )

                            simpleaudio.WaveObject.from_wave_file(
                                "mixkit-basketball-buzzer-1647.wav"
                            ).play()

                            init(autoreset=True)
                            # print(Fore.GREEN + "Execute Trade? (Y/N)")
                            # if input().lower() == "y":
                            print(Fore.GREEN + "\nExecuting Trade...")
                            # flash_dex_a = config[blockchain][xch_path_name[0]][
                            #     "factory"
                            # ]
                            # flash_dex_b = config[blockchain][xch_path_name[1]][
                            #     "router"
                            # ]
                            a_dex = config[blockchain][xch_path_name[0]]["router"]
                            b_dex = config[blockchain][xch_path_name[1]]["router"]
                            # print(
                            #     f"flashPay Args: {base_token}, {other_token}, {trade_amount}, 0, {flash_dex_a}, {flash_dex_b}"
                            # )
                            print(
                                f"Swap Args: {a_dex}, {b_dex}, {trade_path_address[0][1]}, {100 - total_slippage}"
                            )

                            # call trade function
                            percentage = 100 - total_slippage
                            execute_multiSwap(
                                router0=a_dex,
                                router1=b_dex,
                                other_token=trade_path_address[0][1],
                                percentage=percentage,
                                my_address=my_address,
                                trade_amount=trade_amount,
                                trade_amount_raw=trade_amount_raw,
                                contract=arb_contract,
                                url_access=config[blockchain]["url_access"],
                            )
                            print("")
                            print(
                                Fore.GREEN
                                + f"Multiswap completed between {pdex_name} and {sdex_name}"
                            )
                            print(Fore.GREEN + f"Terminating thread")
                            print(
                                Fore.GREEN
                                + "\n#######################################################################################################"
                            )
                            sys.exit()
                            # else:
                            #     print(Fore.GREEN + "\nResuming Scan")
                            #     print(
                            #         Fore.GREEN
                            #         + "\n#######################################################################################################"
                            #     )

                except exceptions.BadFunctionCallOutput as error:
                    print(error)
                    # pass
                    # critical_error = True


def execute_scan(
    blockchain,
    pdex_name,
    sdex_name,
    test_input_amount_raw,
    base_token,
    perc_profit_threshold,
    pool_size_threshold,
    nap_duration,
    assumed_perc_fee,
    trade_amount_raw,
    total_slippage,
    my_address,
):
    # convert to wei
    test_input_amount = Web3.toWei(test_input_amount_raw, "ether")
    trade_amount = Web3.toWei(trade_amount_raw, "ether")

    # get config data
    config = readJson(read_name="repo/config")

    # get list of tokens from milkomeda
    useful_tokens = list(config[blockchain]["tokens"].values())

    # get address for base token
    base_token = config[blockchain]["tokens"][base_token]

    # get factory contract objects
    pfactory_contract = getContractObject(
        address=config[blockchain][pdex_name]["factory"],
        read_name="repo/" + pdex_name + "_" + "factory",
        url_access=config[blockchain]["url_access"],
    )
    sfactory_contract = getContractObject(
        address=config[blockchain][sdex_name]["factory"],
        read_name="repo/" + sdex_name + "_" + "factory",
        url_access=config[blockchain]["url_access"],
    )

    # get router contract objects
    prouter_contract = getContractObject(
        address=config[blockchain][pdex_name]["router"],
        read_name="repo/" + pdex_name + "_router",
        url_access=config[blockchain]["url_access"],
    )
    srouter_contract = getContractObject(
        address=config[blockchain][sdex_name]["router"],
        read_name="repo/" + sdex_name + "_router",
        url_access=config[blockchain]["url_access"],
    )

    # build arb contract object
    arb_contract = getContractObject(
        address=config[blockchain]["bot_contract"]["V1_address"],
        read_name="repo/ArbTraderV1_ABI",
        url_access=config[blockchain]["url_access"],
    )

    # get number of all pairs on primary dex
    all_pairs = pfactory_contract.functions.allPairsLength().call()

    # for i in range(12):
    init(autoreset=True)
    for i in tqdm(
        range(12), Fore.GREEN + f"Searching {pdex_name} and {sdex_name}:", leave=False
    ):
        # take a short nap
        if i > 0:
            tqdm(time.sleep(nap_duration), Fore.RED + "Napping: ", leave=False)

        # scan the blockchain for opportunities
        scan_blockchain(
            all_pairs,
            config,
            blockchain,
            useful_tokens,
            base_token,
            test_input_amount,
            test_input_amount_raw,
            pdex_name,
            sdex_name,
            perc_profit_threshold,
            pfactory_contract,
            sfactory_contract,
            prouter_contract,
            srouter_contract,
            arb_contract,
            pool_size_threshold,
            assumed_perc_fee,
            trade_amount_raw,
            trade_amount,
            total_slippage,
            my_address,
        )


def executeProcess(thread_inputs):
    print("")

    pdex_name = thread_inputs[0]
    sdex_name = thread_inputs[1]
    blockchain = thread_inputs[2]
    test_input_amount_raw = thread_inputs[3]
    trade_amount_raw = thread_inputs[4]
    base_token = thread_inputs[5]
    perc_profit_threshold = thread_inputs[6]
    pool_size_threshold = thread_inputs[7]
    nap_duration = thread_inputs[8]
    assumed_perc_fee = thread_inputs[9]
    total_slippage = thread_inputs[10]
    my_address = thread_inputs[11]

    execute_scan(
        blockchain,
        pdex_name,
        sdex_name,
        test_input_amount_raw,
        base_token,
        perc_profit_threshold,
        pool_size_threshold,
        nap_duration,
        assumed_perc_fee,
        trade_amount_raw,
        total_slippage,
        my_address,
    )


def main():
    # occamx pairs = 37
    # milkyswap pairs = 2302
    # muesliswap = 71

    # user inputs
    pdex_name = "muesliswap"
    sdex_name = "milkyswap"  # "milkyswap" "muesliswap" "occamx"
    blockchain = "milkomeda"
    test_input_amount_raw = 20
    trade_amount_raw = test_input_amount_raw
    base_token = "wada"
    perc_profit_threshold = 1  # 1
    pool_size_threshold = 100000  # 1000
    nap_duration = 10 * 60
    assumed_perc_fee = 0.8
    total_slippage = 1  # this is minimum deviation from expected value accepted
    my_address = "INSERT_WALLET_ADDRESS"

    dexes = {"A": "occamx", "B": "muesliswap", "C": "milkyswap"}
    # A - C   occamx - milkyswap
    # B - C   muesliswap - milkyswap
    # A - B   occamx - muesliswap
    # color_dic = {'yellow':'\033[43m', 'red':'\033[31m', 'blue':'\033[34m', 'end':'\033[0m'}

    print("")
    print("|--------------------------------------------|")
    pdex_name = dexes[input("    Enter Name of Primary Dex: ").upper()]
    while (
        input(
            f"    Primary Dex is \033[1m\033[31m{pdex_name}\033[0m? Confirm: "
        ).lower()
        == "n"
    ):
        pdex_name = dexes[input("    Enter Name of Primary Dex: ").upper()]
    print("|--------------------------------------------|")
    print("")

    print("")
    print("|--------------------------------------------|")
    sdex_name = dexes[input("    Enter Name of Secondary Dex: ").upper()]
    while (
        input(
            f"    Secondary Dex is \033[1m\033[31m{sdex_name}\033[0m? Confirm: "
        ).lower()
        == "n"
    ):
        sdex_name = dexes[input("    Enter Name of Secondary Dex: ").upper()]
    print("|--------------------------------------------|")
    print("")

    input_args = [
        pdex_name,
        sdex_name,
        blockchain,
        test_input_amount_raw,
        trade_amount_raw,
        base_token,
        perc_profit_threshold,
        pool_size_threshold,
        nap_duration,
        assumed_perc_fee,
        total_slippage,
        my_address,
    ]

    print("")
    print("|--------------------------------------------|")
    print("")
    print(f"   Preparing to scan \033[1m{pdex_name} and {sdex_name}\033[0m ...")
    print("")
    print("|--------------------------------------------|")
    print("")

    executeProcess(input_args)


if __name__ == "__main__":
    main()
