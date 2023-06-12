from web3 import Web3
from w3multicall.multicall import W3Multicall

if __name__ == "__main__":

    rpc = 'https://subnets.avax.network/defi-kingdoms/dfk-chain/rpc'

    w3 = Web3(Web3.HTTPProvider(rpc))

    w3_multicall = W3Multicall(w3)

    crystalvale_hero_contract = '0xEb9B61B145D6489Be575D3603F4a704810e143dF'
    crystalvale_questv3_contract = '0x530fff22987E137e7C8D2aDcC4c15eb45b4FA752'
    crystalvale_pet_contract = '0x1990F87d6BC9D9385917E3EDa0A7674411C3Cd7F'

    hero_id = 420
    pet_id = 42


    w3_multicall.add(W3Multicall.Call(
        crystalvale_hero_contract,
        'getHeroV2(uint256)((uint256,(uint256,uint256,uint256,uint256,uint32,uint32),(uint256,uint256,uint8,bool,uint16,uint32,uint32,uint8,uint8,uint8),(uint256,uint256,uint256,uint16,uint64,address,uint8,uint8),(uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16),(uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16),(uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16,uint16),(uint16,uint16,uint16,uint16,uint16,uint16),(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)))',
        hero_id)
    )

    w3_multicall.add(W3Multicall.Call(
        crystalvale_questv3_contract,
        'getCurrentStamina(uint256)(uint256)',
        hero_id)
    )

    w3_multicall.add(W3Multicall.Call(
        crystalvale_pet_contract,
        'isPetHungry(uint256)(bool)',
        pet_id)
    )

    results = w3_multicall.call()

    print("Hero {} lvl={}, xp={}".format(hero_id, results[0][3][3], results[0][3][4]))
    print("Hero {} stamina={}".format(hero_id, results[1]))
    print("Pet {} is{}hungry".format(pet_id, ' ' if results[2] else ' not '))
