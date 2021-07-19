"""
The StrategyResolver is used to perform snaposhot testing after each Vault / Strategy Action.
Make sure to customize the entries below as tests will fail if you don't
"""
from helpers.StrategyCoreResolver import StrategyCoreResolver
from rich.console import Console

console = Console()

class StrategyResolver(StrategyCoreResolver):
    def get_strategy_destinations(self):
        """
        NOTE: Edit this first!!
        Track balances for all strategy implementations
        (Strategy Must Implement)
        """
        # E.G
        # strategy = self.manager.strategy
        # return {
        #     "gauge": strategy.gauge(),
        #     "mintr": strategy.mintr(),
        # }

        return {}

    ## NOTE: All of these will fail unless you extend them!!! 
    def hook_after_confirm_withdraw(self, before, after, params):
        """
            Specifies extra check for ordinary operation on withdrawal
            Use this to verify that balances in the get_strategy_destinations are properly set
        """
        assert True ## This is an optional check you may want to make

    def hook_after_confirm_deposit(self, before, after, params):
        """
            Specifies extra check for ordinary operation on deposit
            Use this to verify that balances in the get_strategy_destinations are properly set
        """
        assert True ## This is an optional check you may want to make

    def hook_after_earn(self, before, after, params):
        """
            Specifies extra check for ordinary operation on earn
            Use this to verify that balances in the get_strategy_destinations are properly set
        """
        assert True ## This is an optional check you may want to make

    def confirm_harvest(self, before, after, tx):
        """
            Verfies that the Harvest produced yield and fees
        """
        assert False ## You must implement this
        
        ## For basic strats the code below is sufficient
        console.print("=== Compare Harvest ===")
        self.manager.printCompare(before, after)
        self.confirm_harvest_state(before, after, tx)

        valueGained = after.get("vault.pricePerShare") > before.get(
            "vault.pricePerShare"
        )

        # # Strategist should earn if fee is enabled and value was generated
        # if before.get("strategy.performanceFeeStrategist") > 0 and valueGained:
        #     assert after.balances("want", "strategist") > before.balances(
        #         "want", "strategist"
        #     )

        # # Strategist should earn if fee is enabled and value was generated
        # if before.get("strategy.performanceFeeGovernance") > 0 and valueGained:
        #     assert after.balances("want", "governanceRewards") > before.balances(
        #         "want", "governanceRewards"
        #     )

    def confirm_tend(self, before, after, tx):
        """
        Tend Should;
        - Increase the number of staked tended tokens in the strategy-specific mechanism
        - Reduce the number of tended tokens in the Strategy to zero

        (Strategy Must Implement)
        """
        assert False ## You must implement this


