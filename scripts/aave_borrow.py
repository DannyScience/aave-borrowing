from brownie import interface, network, config
from scripts.helpfull_scripts import get_account
from scripts.get_weth import get_weth
from web3 import Web3


AMOUNT = Web3.toWei(0.1, 'ether')


def get_lending_pool():
    lending_pool_addresses_provider = interface.IPoolAddressesProvider(
        config['networks'][network.show_active()]['pool_addresses_provider']
    )
    lending_pool_address = lending_pool_addresses_provider.getPool()
    lending_pool = interface.IPool(lending_pool_address)
    return lending_pool


def approve_erc20(spender, amount, erc20_address, account):
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {'from': account})
    tx.wait(1)
    print('ERC20 approved')
    return tx


def get_account_data(user_address, lending_pool):
    (
        total_collateral_base,
        total_debt_base,
        available_borrows_base,
        current_liquidation_threshold,
        ltv,
        health_factor
    ) = lending_pool.getUserAccountData(user_address)
    total_collateral_base = Web3.fromWei(total_collateral_base, 'ether')
    total_debt_base = Web3.fromWei(total_debt_base, 'ether')
    available_borrows_base = Web3.fromWei(available_borrows_base, 'ether')
    print(f'''Total collateral: {total_collateral_base}
          Total debt: {total_debt_base}
          Available borrows: {available_borrows_base}''')
    return (float(total_debt_base), float(available_borrows_base))
    

def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_latest_price}")
    return float(converted_latest_price)


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)

    print("Repaid!")


def main():
    account = get_account()
    erc20_address = config['networks'][network.show_active()]['weth_token']
    if network.show_active() in ["mainnet-fork"]:
        get_weth()
    lending_pool = get_lending_pool()
    
    approve_erc20(lending_pool.address, AMOUNT, erc20_address, account)
    
    tx = lending_pool.deposit(erc20_address, 10000000000000000, account.address, 0, {'from': account, 'gas_limit': 50000000})
    tx.wait(1)
    print('Deposited to lending pool')
    debt, available_borrows = get_account_data(account.address, lending_pool)
        
    dai_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed"]
    )
    amount_dai_to_borrow = (1 / dai_eth_price) * (available_borrows * 0.95)
    print(f"We are going to borrow {amount_dai_to_borrow} DAI")
    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("Borrowed some DAI!")
    get_account_data(account.address, lending_pool)
    
    repay_all(Web3.toWei(amount_dai_to_borrow, "ether"), lending_pool, account)
    get_account_data(account.address, lending_pool)
