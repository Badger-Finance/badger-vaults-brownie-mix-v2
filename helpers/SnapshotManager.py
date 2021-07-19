from brownie import *
from tabulate import tabulate
from rich.console import Console
from helpers.multicall import Multicall
from helpers.utils import val

from helpers.snapshot.snap import Snap

from tests.StrategyResolver import (
    StrategyResolver
)

console = Console()

class SnapshotManager:
    def __init__(self, vault, strategy, key):
        self.key = key
        self.vault = vault
        self.strategy = strategy
        self.want = interface.IERC20(self.vault.token())
        self.resolver = self.init_resolver()
        self.snaps = {}
        self.settSnaps = {}
        self.entities = {}

        assert self.want == self.strategy.want()

        # Common entities for all strategies
        self.addEntity("vault", self.vault.address)
        self.addEntity("strategy", self.strategy.address)

        ## Accounts TODO: Fix Origin to vault
        self.addEntity("governance", self.vault.governance())
        self.addEntity("management", self.vault.management())
        self.addEntity("guardian", self.vault.guardian())
        self.addEntity("vaultRewards", self.vault.rewards())
        self.addEntity("stratRewards", self.strategy.rewards())
        self.addEntity("keeper", self.strategy.keeper())
        self.addEntity("strategist", self.strategy.strategist())

        destinations = self.resolver.get_strategy_destinations()
        for key, dest in destinations.items():
            self.addEntity(key, dest)

    def add_snap_calls(self, entities):
        calls = []
        calls = self.resolver.add_balances_snap(calls, entities)
        calls = self.resolver.add_sett_snap(calls)
        # calls = self.resolver.add_sett_permissions_snap(calls)
        calls = self.resolver.add_strategy_snap(calls, entities=entities)
        return calls

    def snap(self, trackedUsers=None):
        print("snap")
        snapBlock = chain.height
        entities = self.entities

        if trackedUsers:
            for key, user in trackedUsers.items():
                entities[key] = user

        calls = self.add_snap_calls(entities)

        multi = Multicall(calls)
        # multi.printCalls()

        data = multi()
        self.snaps[snapBlock] = Snap(
            data,
            snapBlock,
            [x[0] for x in entities.items()],
        )

        return self.snaps[snapBlock]

    def addEntity(self, key, entity):
        self.entities[key] = entity

    def init_resolver(self):
        return StrategyResolver(self)

    def settTend(self, overrides, confirm=True):
        user = overrides["from"].address
        trackedUsers = {"user": user}
        before = self.snap(trackedUsers)
        tx = self.strategy.tend(overrides)
        after = self.snap(trackedUsers)
        if confirm:
            self.resolver.confirm_tend(before, after, tx)

    def settHarvest(self, overrides, confirm=True):
        user = overrides["from"].address
        trackedUsers = {"user": user}
        before = self.snap(trackedUsers)
        tx = self.strategy.harvest(overrides)
        after = self.snap(trackedUsers)
        if confirm:
            self.resolver.confirm_harvest(before, after, tx)

    def settDeposit(self, amount, overrides, confirm=True):
        user = overrides["from"].address
        trackedUsers = {"user": user}
        before = self.snap(trackedUsers)
        self.vault.deposit(amount, overrides)
        after = self.snap(trackedUsers)
        print("In settDepositxrwrw")
        if confirm:
            self.resolver.confirm_deposit(
                before, after, {"user": user, "amount": amount}
            )

    def settDepositAll(self, overrides, confirm=True):
        user = overrides["from"].address
        trackedUsers = {"user": user}
        userBalance = self.want.balanceOf(user)
        before = self.snap(trackedUsers)
        self.vault.deposit(overrides)
        after = self.snap(trackedUsers)
        if confirm:
            self.resolver.confirm_deposit(
                before, after, {"user": user, "amount": userBalance}
            )


    def settWithdraw(self, amount, overrides, confirm=True):
        user = overrides["from"].address
        trackedUsers = {"user": user}
        before = self.snap(trackedUsers)
        tx = self.vault.withdraw(amount, overrides)
        after = self.snap(trackedUsers)
        if confirm:
            self.resolver.confirm_withdraw(
                before, after, {"user": user, "amount": amount}, tx
            )

    def settWithdrawAll(self, overrides, confirm=True):
        user = overrides["from"].address
        trackedUsers = {"user": user}
        userBalance = self.vault.balanceOf(user)
        before = self.snap(trackedUsers)
        tx = self.vault.withdraw(userBalance, overrides)
        after = self.snap(trackedUsers)

        if confirm:
            self.resolver.confirm_withdraw(
                before, after, {"user": user, "amount": userBalance}, tx
            )

    def format(self, key, value):
        if type(value) is int:
            if "stakingRewards.staked" or "stakingRewards.earned" in key:
                return val(value)
            # Ether-scaled balances
            # TODO: Handle based on token decimals
            if (
                "balance" in key
                or key == "vault.totalDebt" ## Instead of available
                or key == "vault.pricePerShare" ## Instead of pricePerShare
                or key == "vault.totalSupply"
            ):
                return val(value)
        return value

    def diff(self, a, b):
        if type(a) is int and type(b) is int:
            return b - a
        else:
            return "-"

    def printCompare(self, before: Snap, after: Snap):
        # self.printPermissions()
        table = []
        console.print(
            "[green]=== Compare: {} Vault {} -> {} ===[/green]".format(
                self.key, before.block, after.block
            )
        )

        for key, item in before.data.items():

            a = item
            b = after.get(key)

            # Don't add items that don't change
            if a != b:
                table.append(
                    [
                        key,
                        self.format(key, a),
                        self.format(key, b),
                        self.format(key, self.diff(a, b)),
                    ]
                )

        print(
            tabulate(
                table, headers=["metric", "before", "after", "diff"], tablefmt="grid"
            )
        )

    ## TODO: Check again and change names and keys
    def printPermissions(self):
        # Accounts
        table = []
        console.print("[blue]=== Permissions: {} Vault ===[/blue]".format(self.key))

        table.append(["vault.keeper", self.vault.keeper()])
        table.append(["vault.governance", self.vault.governance()])
        table.append(["vault.strategist", self.vault.strategist()])

        table.append(["---------------", "--------------------"])

        table.append(["strategy.keeper", self.strategy.keeper()])
        table.append(["strategy.governance", self.strategy.governance()])
        table.append(["strategy.strategist", self.strategy.strategist()])
        table.append(["strategy.guardian", self.strategy.guardian()])

        table.append(["---------------", "--------------------"])
        print(tabulate(table, headers=["account", "value"]))

    def printBasics(self, snap: Snap):
        table = []
        console.print("[green]=== Status Report: {} Vault ===[green]".format(self.key))

        table.append(["vault.pricePerShare", snap.get("vault.pricePerShare")])
        table.append(["strategy.want", snap.balances("want", "strategy")])

        print(tabulate(table, headers=["metric", "value"]))

    def printTable(self, snap: Snap):
        # Numerical Data
        table = []
        console.print("[green]=== Status Report: {} Vault ===[green]".format(self.key))

        for key, item in snap.data.items():
            # Don't display 0 balances:
            if "balances" in key and item == 0:
                continue
            table.append([key, self.format(key, item)])

        table.append(["---------------", "--------------------"])
        print(tabulate(table, headers=["metric", "value"]))
