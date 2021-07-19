import brownie
from brownie import *
from helpers.constants import MaxUint256
from helpers.SnapshotManager import SnapshotManager
from helpers.time import days

def test_deposit_withdraw_single_user_flow(user, amount, vault, strategy, want, keeper):
    # Setup
    snap = SnapshotManager(vault, strategy, "StrategySnapshot")
    randomUser = accounts[6]
    #End Setup

    depositAmount = int(amount * 0.8)
    assert depositAmount > 0

    want.approve(vault.address, MaxUint256, {"from": user})

    snap.settDeposit(depositAmount, {"from": user})
    
    shares = vault.balanceOf(user)

    # Earn
    with brownie.reverts("!authorized"):
        snap.settHarvest({"from": randomUser})

    snap.settHarvest({"from": keeper})

    chain.sleep(15)
    chain.mine(1)

    snap.settWithdraw(shares // 2, {"from": user})

    chain.sleep(10000)
    chain.mine(1)

    snap.settWithdraw(shares // 2 - 1, {"from": user})



def test_single_user_harvest_flow(user, vault, strategy, want, keeper):
    # Setup
    snap = SnapshotManager(vault, strategy, "StrategySnapshot")
    randomUser = accounts[6]
    startingBalance = want.balanceOf(user)
    depositAmount = startingBalance // 2
    assert startingBalance >= depositAmount
    assert startingBalance >= 0
    # End Setup

    # Deposit
    want.approve(vault, MaxUint256, {"from": user})
    snap.settDeposit(depositAmount, {"from": user})
    shares = vault.balanceOf(user)


    assert want.balanceOf(vault) > 0
    print("want.balanceOf(vault)", want.balanceOf(vault))

    # First Harvest to start earning
    snap.settHarvest({"from": keeper})

    # Tend
    with brownie.reverts("!authorized"):
        strategy.tend({"from": randomUser})

    snap.settTend({"from": keeper})

    chain.sleep(days(0.5))
    chain.mine()

    snap.settTend({"from": keeper})

    chain.sleep(days(1))
    chain.mine()

    with brownie.reverts("!authorized"):
        strategy.harvest({"from": randomUser})

    snap.settHarvest({"from": keeper})

    chain.sleep(days(1))
    chain.mine()

    snap.settTend({"from": keeper})

    snap.settWithdraw(shares // 2, {"from": user})

    chain.sleep(days(3))
    chain.mine()

    snap.settHarvest({"from": keeper})
    snap.settWithdraw(shares // 2 - 1, {"from": user})


def test_migrate_single_user(user, vault, strategy, want, strategist, gov):
    # Setup
    randomUser = accounts[6]
    snap = SnapshotManager(vault, strategy, "StrategySnapshot")

    startingBalance = want.balanceOf(user)
    depositAmount = startingBalance // 2
    assert startingBalance >= depositAmount
    # End Setup

    # Deposit
    want.approve(vault, MaxUint256, {"from": user})
    snap.settDeposit(depositAmount, {"from": user})

    chain.sleep(15)
    chain.mine()

    ## Load funds
    strategy.harvest({"from": strategist})

    chain.snapshot()

    # Test no harvests
    chain.sleep(days(2))
    chain.mine()

    before = {"settWant": want.balanceOf(vault), "stratWant": strategy.estimatedTotalAssets()}

    # Withdraw from strat via revoking it, NOTE: can also be done by setting it's debt to 0
    with brownie.reverts():
        vault.revokeStrategy(strategy, {"from": randomUser})
    ## Set debt limit to zero so on next harvest all funds will be withdrawn
    vault.revokeStrategy(strategy, {"from": gov})
    strategy.harvest() ## Harvest to wihdraw funds

    after = {"settWant": want.balanceOf(vault), "stratWant": strategy.estimatedTotalAssets()}

    assert after["settWant"] > before["settWant"]
    assert after["stratWant"] < before["stratWant"]
    assert after["stratWant"] == 0

    # Test tend only
    chain.revert()

    chain.sleep(days(2))
    chain.mine()

    strategy.tend({"from": gov})

    before = {"settWant": want.balanceOf(vault), "stratWant": strategy.estimatedTotalAssets()}

    # Withdraw from strat via revoking it, NOTE: can also be done by setting it's debt to 0
    ## Set debt limit to zero so on next harvest all funds will be withdrawn
    vault.revokeStrategy(strategy, {"from": gov})
    strategy.harvest() ## Harvest to wihdraw funds

    after = {"settWant": want.balanceOf(vault), "stratWant": strategy.estimatedTotalAssets()}

    assert after["settWant"] > before["settWant"]
    assert after["stratWant"] < before["stratWant"]
    assert after["stratWant"] == 0

    # Test harvest, with tend if tendable
    chain.revert()

    chain.sleep(days(1))
    chain.mine()

    strategy.tend({"from": gov})

    chain.sleep(days(1))
    chain.mine()

    before = {
        "settWant": want.balanceOf(vault),
        "stratWant": strategy.estimatedTotalAssets(),
        # "rewardsWant": want.balanceOf(controller.rewards()), ## TODO: Test for rewards growth
    }

    # Withdraw from strat via revoking it, NOTE: can also be done by setting it's debt to 0
    ## Set debt limit to zero so on next harvest all funds will be withdrawn
    vault.revokeStrategy(strategy, {"from": gov})
    strategy.harvest() ## Harvest to wihdraw funds

    after = {"settWant": want.balanceOf(vault), "stratWant": strategy.estimatedTotalAssets()}

    assert after["settWant"] > before["settWant"]
    assert after["stratWant"] < before["stratWant"]
    assert after["stratWant"] == 0



def test_single_user_harvest_flow_remove_fees(user, vault, strategy, want, keeper):
    # Setup
    randomUser = accounts[6]
    snap = SnapshotManager(vault, strategy, "StrategySnapshot")
    startingBalance = want.balanceOf(user)
    tendable = True
    startingBalance = want.balanceOf(user)
    depositAmount = startingBalance // 2
    assert startingBalance >= depositAmount
    # End Setup

    # Deposit
    want.approve(vault, MaxUint256, {"from": user})
    snap.settDeposit(depositAmount, {"from": user})

    # Earn
    snap.settHarvest({"from": keeper})

    chain.sleep(days(0.5))
    chain.mine()

    if tendable:
        snap.settTend({"from": keeper})

    chain.sleep(days(1))
    chain.mine()

    with brownie.reverts("!authorized"):
        strategy.harvest({"from": randomUser})


    snap.settHarvest({"from": keeper})

    chain.sleep(days(1))
    chain.mine()

    if tendable:
        snap.settTend({"from": keeper})

    chain.sleep(days(3))
    chain.mine()

    snap.settHarvest({"from": keeper})

    snap.settWithdrawAll({"from": user})

    endingBalance = want.balanceOf(user)

    print("Report after 4 days")
    print("Gains")
    print(endingBalance - startingBalance)
    print("gainsPercentage")
    print((endingBalance - startingBalance) / startingBalance)
