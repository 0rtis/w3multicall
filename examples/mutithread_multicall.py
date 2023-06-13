import sys
import logging
from web3 import Web3
from w3multicall.multicall import W3Multicall
from w3multicall.web3.web3 import W3, W3Pool
from w3multicall.threading.w3multicall_executor import W3MulticallExecutor

if __name__ == "__main__":
    log_format = '[%(levelname)s] %(asctime)s|%(name)s|%(threadName)s|%(filename)s:%(lineno)d: %(message)s'

    logger = logging.getLogger("Multithread multicall")
    logger.setLevel(logging.INFO)
    logging.basicConfig(level=logging.DEBUG, format=log_format, stream=sys.stdout)

    logging.getLogger("web3.providers.HTTPProvider").disabled = True
    logging.getLogger("web3._utils.request").disabled = True
    logging.getLogger("urllib3.connectionpool").disabled = True
    logging.getLogger("web3.RequestManager").disabled = True

    w3_pool = W3Pool([
        W3(Web3(Web3.HTTPProvider('https://eth-rpc.gateway.pokt.network')), delay_between_call=5),
        W3(Web3(Web3.HTTPProvider('https://ethereum.publicnode.com')), delay_between_call=5),
        W3(Web3(Web3.HTTPProvider('https://rpc.flashbots.net/')), delay_between_call=5)
    ], logger)

    executor = W3MulticallExecutor(w3_pool, len(w3_pool.w3s), logger=logger)

    bayc_futures = []
    azuki_futures = []
    moonbird_futures = []
    for i in range(1, 10):

        bayc_futures.append(executor.submit(W3Multicall.Call(
            '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D',  # BAYC NFT contract address
            'ownerOf(uint256)(address)',
            i)))

        azuki_futures.append(executor.submit(W3Multicall.Call(
            '0xED5AF388653567Af2F388E6224dC7C4b3241C544',  # Azuki NFT contract address
            'ownerOf(uint256)(address)',
            i)))

        moonbird_futures.append(executor.submit(W3Multicall.Call(
            '0x23581767a106ae21c074b2276D25e5C3e136a68b',  # Moonbird NFT contract address
            'ownerOf(uint256)(address)',
            i)))

    for i in range(len(bayc_futures)):
        print("The owner of the BAYC Nº{} is {}".format(i + 1, bayc_futures[i].get()))

    for i in range(len(azuki_futures)):
        print("The owner of the Azuki Nº{} is {}".format(i + 1, azuki_futures[i].get()))

    for i in range(len(moonbird_futures)):
        print("The owner of the Moonbird Nº{} is {}".format(i + 1, moonbird_futures[i].get()))

