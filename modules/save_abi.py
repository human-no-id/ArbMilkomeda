# based on info from config get and save abi
from modules import store_new_abi

DEX_NAME = "milkyswap"
ABI_TYPE = "router"
BLOCKCHAIN = "milkomeda"

store_new_abi(dex_name=DEX_NAME, abi_type=ABI_TYPE, blockchain=BLOCKCHAIN)
