
[![Pypi_repo](https://img.shields.io/pypi/v/w3multicall?style=flat-square)](https://pypi.org/project/w3multicall/)
[![GitHub license](https://img.shields.io/github/license/0rtis/w3multicall.svg?style=flat-square)](https://github.com/0rtis/w3multicall/blob/master/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/0rtis?style=flat-square)](https://github.com/0rtis)
[![Follow @twitter handle](https://img.shields.io/twitter/follow/Knockturn_io.svg?style=flat-square)](https://twitter.com/intent/follow?screen_name=ortis95)


Install with `pip install w3multicall`

https://pypi.org/project/w3multicall/


**Want to support this project ? You can help us by:**
- Delegating AVAX to our Avalanche node **NodeID-4btZGj8TmrycK22kwgBK5wJEFighAFWiZ**
- Making a donation to **0xA68fBfa3E0c86D1f3fF071853df6DAe8753095E2**


*This software is derived from [multicall.py](https://github.com/banteg/multicall.py).
However, [multicall.py](https://github.com/banteg/multicall.py) is built on [asyncio](https://docs.python.org/3/library/asyncio.html) and
[does not support multi-threading](https://github.com/banteg/multicall.py/issues/77)*

This implementation fixes that.

# Multicall Smart Contract
[Multicall](https://github.com/mds1/multicall) smart contract are deployed on numerous chains and can help reduce the strain
put on RPC by order of magnitude by *batching* multiple requests into one.

# Simple Multicall

```
from web3 import Web3
from w3multicall.multicall import W3Multicall

w3 = Web3(Web3.HTTPProvider(rpc))

w3_multicall = W3Multicall(w3)

w3_multicall.add(W3Multicall.Call(
    '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',  # USDC contract address
    'balanceOf(address)(uint256)',  # method signature to call
    '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045')  # vitalik.eth
)

results = w3_multicall.call()

print("Vitalik holds {:.2f} USDC".format(results[0]/10**6))

```

[See full example](/examples/simple_multicall.py)

# Multithread Multicall

```
w3_pool = W3Pool([
        W3(Web3(Web3.HTTPProvider('https://eth-rpc.gateway.pokt.network')), 5),
        W3(Web3(Web3.HTTPProvider('https://ethereum.publicnode.com')), 5),
        W3(Web3(Web3.HTTPProvider('https://rpc.flashbots.net/')), 5)
    ], logger)

executor = W3MulticallExecutor(w3_pool, processes=len(w3_pool.w3s))

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
```

[See full example](/examples/mutithread_multicall.py)