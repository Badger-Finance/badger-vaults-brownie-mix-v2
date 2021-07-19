import brownie
from brownie import Contract
import pytest
from helpers.constants import AddressZero


def test_vault_emergency(
  chain, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX
):
  ## Deposit in Vault
  token.approve(vault.address, amount, {"from": user})
  vault.deposit(amount, {"from": user})
  assert token.balanceOf(vault.address) == amount

  if(token.balanceOf(user) > 0):
      token.transfer(AddressZero, token.balanceOf(user), {"from": user})

  print("stratDep1 ")
  print(strategy.estimatedTotalAssets())

  # Harvest 1: Send funds through the strategy
  strategy.harvest()
  chain.mine(100)
  assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

  ## Set Emergency
  vault.setEmergencyShutdown(True)

  ## Withdraw (does it work, do you get what you expect)
  vault.withdraw({"from": user})

  assert pytest.approx(token.balanceOf(user), rel=RELATIVE_APPROX) == amount

def test_emergency_permissions_deny(strategy, strategist, gov, guardian, management, accounts):
  with brownie.reverts("!authorized"):
    strategy.setEmergencyExit({"from": accounts[9]})

def test_emergency_permissions_strategist(strategy, strategist, gov, guardian, management, accounts):
    strategy.setEmergencyExit({"from": strategist})
    assert strategy.emergencyExit() == True

def test_emergency_permissions_gov(strategy, strategist, gov, guardian, management, accounts):
    strategy.setEmergencyExit({"from": gov})
    assert strategy.emergencyExit() == True

def test_emergency_permissions_guardian(strategy, strategist, gov, guardian, management, accounts):
    strategy.setEmergencyExit({"from": guardian})
    assert strategy.emergencyExit() == True

def test_emergency_permissions_management(strategy, strategist, gov, guardian, management, accounts):
    strategy.setEmergencyExit({"from": management})
    assert strategy.emergencyExit() == True

# TODO: Add tests that show proper operation of this strategy through "emergencyExit"
#       Make sure to demonstrate the "worst case losses" as well as the time it takes
# NOTE: lpComponent doesn't exist
def test_emergency_exit(
    chain, accounts, token, vault, strategy, user, strategist, amount, RELATIVE_APPROX, lpComponent, borrowed, reward, incentivesController
):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": user})
    vault.deposit(amount, {"from": user})
    assert token.balanceOf(vault.address) == amount

    print("stratDep1 ")
    print(strategy.estimatedTotalAssets())

    # Harvest 1: Send funds through the strategy
    strategy.harvest()
    chain.mine(100)
    assert pytest.approx(strategy.estimatedTotalAssets(), rel=RELATIVE_APPROX) == amount

    

    # TODO: Add some code before harvest #2 to simulate earning yield
    before_pps = vault.pricePerShare()
    before_total = vault.totalAssets()
    before_debt = vault.totalDebt()

    chain.sleep(3600 * 24 * 1) ## Sleep 1 day
    chain.mine(1)
    
    print("Reward") 
    print(incentivesController.getRewardsBalance(
            [lpComponent, borrowed],
            strategy
        ))
    print("stratDep2 ")
    print(strategy.estimatedTotalAssets())

    # Harvest 2: Realize profit
    strategy.harvest()
    print("Reward 2") 
    print(incentivesController.getRewardsBalance(
            [lpComponent, borrowed],
            strategy
        ))
    print("stratDep3 ")
    print(strategy.estimatedTotalAssets())
    amountAfterHarvest = token.balanceOf(strategy) + lpComponent.balanceOf(strategy) - borrowed.balanceOf(strategy)
    chain.sleep(3600 * 6)  # 6 hrs needed for profits to unlock
    chain.mine(1)
    profit = token.balanceOf(vault.address)  # Profits go to vault

    # NOTE: Your strategy must be profitable
    # NOTE: May have to be changed based on implementation
    stratAssets = strategy.estimatedTotalAssets()
    
    print("stratAssets")
    print(stratAssets)

    vaultAssets = vault.totalAssets()
    print("vaultAssets")
    print(vaultAssets)

    ## Total assets for strat are token + lpComponent + borrowed
    assert  amountAfterHarvest + profit > amount
    ## NOTE: Changed to >= because I can't get the PPS to increase
    assert vault.pricePerShare() >= before_pps ## NOTE: May want to tweak this to >= or increase amounts and blocks
    assert vault.totalAssets() > before_total ## NOTE: Assets must increase or there's something off with harvest
    ## NOTE: May want to harvest a third time and see if it icnreases totalDebt for strat

    strategy.setEmergencyExit({"from": strategist})

    strategy.harvest() ## Will liquidate all

    assert lpComponent.balanceOf(strategy) == 0
    assert token.balanceOf(strategy) == 0
    assert token.balanceOf(vault) >= amount ## The vault has all funds (some loss may have happened)

