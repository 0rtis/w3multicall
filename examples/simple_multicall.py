from web3 import Web3
from w3multicall.multicall import W3Multicall

if __name__ == "__main__":

    rpc = 'https://ethereum.publicnode.com'

    w3 = Web3(Web3.HTTPProvider(rpc))

    w3_multicall = W3Multicall(w3)

    w3_multicall.add(W3Multicall.Call(
        '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',  # USDC contract address
        'balanceOf(address)(uint256)',  # method signature to call
        '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')  # vitalik.eth
    )

    w3_multicall.add(W3Multicall.Call(
        '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D',  # BAYC NFT contract address
        'ownerOf(uint256)(address)',  # method signature to call
        1)
    )

    w3_multicall.add(W3Multicall.Call(
        '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH contract address
        'totalSupply()(uint256)'  # method to call
        )
    )

    results = w3_multicall.call()

    print("Vitalik holds {:.2f} USDC".format(results[0]/10**6))
    print("The owner of the first BAYC NFT is {}".format(results[1]))
    print("The current supply of WETH is {:.2f}".format(results[2] / 10 ** 18))