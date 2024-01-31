from brownie import interface, network, config
from scripts.helpfull_scripts import get_account
    

def get_weth(amount=0.2):
    account = get_account()
    weth = interface.IWeth(config['networks'][network.show_active()]['weth_token'])
    tx = weth.deposit({'from': account, 'value': amount * 10 ** 18})
    print(f'Deposited {amount} ETH into WETH')
    return tx


def main():
    get_weth()
