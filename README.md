# Badger Vaults Brownie Mix (V2)

## TODO:
- Use Scripts from Vaults Code, rather than copy pasting
- Write Scripts to add to registry
- Simplify Config by using config file for all setup
- Figure out deployment on various networks
- Add UI to quickly debug Strategy and Vault

## What you'll find here

This is the architecture for Badger V2 (using Yearn V2 architecture)

- Basic Solidity Smart Contract for creating your own Badger Strategy ([`contracts/Strategy.sol`](contracts/Strategy.sol))

- Interfaces for some of the most used DeFi protocols on ethereum mainnet. ([`interfaces`](interfaces))
- Dependencies for OpenZeppelin and other libraries. ([`deps`](deps))

- Sample test suite that runs on mainnet fork. ([`tests`](tests))

This mix is configured for use with [Ganache](https://github.com/trufflesuite/ganache-cli) on a [forked mainnet](https://eth-brownie.readthedocs.io/en/stable/network-management.html#using-a-forked-development-network).

## Installation and Setup

1. Use this code by clicking on Use This Template

2. Download the code with ```git clone URL_FROM_GITHUB```

3. [Install Brownie](https://eth-brownie.readthedocs.io/en/stable/install.html) & [Ganache-CLI](https://github.com/trufflesuite/ganache-cli), if you haven't already.

4. Copy the `.env.example` file, and rename it to `.env`

5. Sign up for [Infura](https://infura.io/) and generate an API key. Store it in the `WEB3_INFURA_PROJECT_ID` environment variable.

6. Sign up for [Etherscan](www.etherscan.io) and generate an API key. This is required for fetching source codes of the mainnet contracts we will be interacting with. Store the API key in the `ETHERSCAN_TOKEN` environment variable.

7. Install the dependencies in the package
```bash
## Javascript dependencies
npm i

## Python Dependencies
pip install virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Basic Use. NOTE: WRONG

To deploy the demo Badger Strategy in a development environment:

1. Open the Brownie console. This automatically launches Ganache on a forked mainnet.

```bash
  brownie console
```

2. Run Scripts for Deployment
```
  brownie run deploy
```

Deployment will set up a Vault, Controller and deploy your strategy

3. Run the test deployment in the console and interact with it
```python
  brownie console
  deployed = run("deploy")

  ## Takes a minute or so
  Transaction sent: 0xa0009814d5bcd05130ad0a07a894a1add8aa3967658296303ea1f8eceac374a9
  Gas price: 0.0 gwei   Gas limit: 12000000   Nonce: 9
  UniswapV2Router02.swapExactETHForTokens confirmed - Block: 12614073   Gas used: 88626 (0.74%)

  ## Now you can interact with the contracts via the console
  >>> deployed
  {
      'controller': 0x602C71e4DAC47a042Ee7f46E0aee17F94A3bA0B6,
      'deployer': 0x66aB6D9362d4F35596279692F0251Db635165871,
      'lpComponent': 0x028171bCA77440897B824Ca71D1c56caC55b68A3,
      'rewardToken': 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9,
      'sett': 0x6951b5Bd815043E3F842c1b026b0Fa888Cc2DD85,
      'strategy': 0x9E4c14403d7d9A8A782044E86a93CAE09D7B2ac9,
      'vault': 0x6951b5Bd815043E3F842c1b026b0Fa888Cc2DD85,
      'want': 0x6B175474E89094C44Da98b954EedeAC495271d0F
  }
  >>>

  ## Deploy also uniswaps want to the deployer (accounts[0]), so you have funds to play with!
  >>> deployed.want.balanceOf(a[0])
  240545908911436022026

```

## Adding Configuration: NOTE: NO RESOLVERS, NO CONFIG YET

To ship a valid strategy, that will be evaluated to deploy on mainnet, with potentially $100M + in TVL, you need to:
1. Write the Strategy Code in Strategy.sol
2. Customize the StrategyResolver so that snapshot testing can verify that operations happened correctly
3. Write any extra test to confirm that the strategy is working properly

## Implementing Strategy Logic

[`contracts/Strategy.sol`](contracts/Strategy.sol) is where you implement your own logic for your strategy. In particular:

* Create a descriptive name for your strategy via `Strategy.name()`.
* Invest your want tokens via `Strategy.adjustPosition()`.
* Take profits and report losses via `Strategy.prepareReturn()`.
* Unwind enough of your position to payback withdrawals via `Strategy.liquidatePosition()`.
* Unwind all of your positions via `Strategy.exitPosition()`.
* Fill in a way to estimate the total `want` tokens managed by the strategy via `Strategy.estimatedTotalAssets()`.
* Migrate all the positions managed by your strategy via `Strategy.prepareMigration()`.
* Make a list of all position tokens that should be protected against movements via `Strategy.protectedTokens()`.


## Specifying checks for ordinary operations in config/StrategyResolver
In order to snapshot certain balances, we use the Snapshot manager.
This class helps with verifying that ordinary procedures (deposit, withdraw, harvest), happened correctly.

See `/helpers/StrategyCoreResolver.py` for the base resolver that all strategies use
Edit `/config/StrategyResolver.py` to specify and verify how an ordinary harvest should behave

### StrategyResolver

* Add Contract to check balances for in `get_strategy_destinations` (e.g. deposit pool, gauge, lpTokens)
* Write `confirm_harvest` to verify that the harvest was profitable
* Write `confirm_tend` to verify that tending will properly rebalance the strategy
* Specify custom checks for ordinary deposits, withdrawals and calls to `earn` by setting up `hook_after_confirm_withdraw`, `hook_after_confirm_deposit`, `hook_after_earn`

## Add your custom testing
Check the various tests under `/tests`
The file `/tests/test_custom` is already set up for you to write custom tests there
See example tests in `/tests/examples`
All of the tests need to pass!
If a test doesn't pass, you better have a great reason for it!

## Testing

To run the tests:

```
brownie test
```


## Debugging Failed Transactions

Use the `--interactive` flag to open a console immediatly after each failing test:

```
brownie test --interactive
```

Within the console, transaction data is available in the [`history`](https://eth-brownie.readthedocs.io/en/stable/api-network.html#txhistory) container:

```python
>>> history
[<Transaction '0x50f41e2a3c3f44e5d57ae294a8f872f7b97de0cb79b2a4f43cf9f2b6bac61fb4'>,
 <Transaction '0xb05a87885790b579982983e7079d811c1e269b2c678d99ecb0a3a5104a666138'>]
```

Examine the [`TransactionReceipt`](https://eth-brownie.readthedocs.io/en/stable/api-network.html#transactionreceipt) for the failed test to determine what went wrong. For example, to view a traceback:

```python
>>> tx = history[-1]
>>> tx.traceback()
```

To view a tree map of how the transaction executed:

```python
>>> tx.call_trace()
```

See the [Brownie documentation](https://eth-brownie.readthedocs.io/en/stable/core-transactions.html) for more detailed information on debugging failed transactions.


## Deployment

When you are finished testing and ready to deploy to the mainnet:

1. [Import a keystore](https://eth-brownie.readthedocs.io/en/stable/account-management.html#importing-from-a-private-key) into Brownie for the account you wish to deploy from.
2. Run [`scripts/deploy.py`](scripts/deploy.py) with the following command

```bash
$ brownie run deployment --network mainnet
```

You will be prompted to enter your keystore password, and then the contract will be deployed.


## Known issues

### No access to archive state errors

If you are using Ganache to fork a network, then you may have issues with the blockchain archive state every 30 minutes. This is due to your node provider (i.e. Infura) only allowing free users access to 30 minutes of archive state. To solve this, upgrade to a paid plan, or simply restart your ganache instance and redploy your contracts.

# Resources

- Badger [Discord channel](https://discord.gg/phbqWTCjXU)
- Yearn [Discord channel](https://discord.com/invite/6PNv2nF/)
- Brownie [Gitter channel](https://gitter.im/eth-brownie/community)
- Alex The Entreprenerd on [Twitter](https://twitter.com/GalloDaSballo)


# TODO: Take the logic to enable and deploy a strategy and add above
## Basic Use YEARN

To deploy the demo Yearn Strategy in a development environment:

1. Open the Brownie console. This automatically launches Ganache on a forked mainnet.

```bash
$ brownie console
```

2. Create variables for the Yearn Vault and Want Token addresses. These were obtained from the Yearn Registry. Also, loan the Yearn governance multisig.

```python
>>> vault = Vault.at("0xBFa4D8AA6d8a379aBFe7793399D3DdaCC5bBECBB")  # yvDAI (v0.2.2)
>>> token = Token.at("0x6b175474e89094c44da98b954eedeac495271d0f")  # DAI
>>> gov = "ychad.eth"  # ENS for Yearn Governance Multisig
```

3. Deploy the [`Strategy.sol`](contracts/Strategy.sol) contract.

```python
>>> strategy = Strategy.deploy(vault, {"from": accounts[0]})
Transaction sent: 0xc8a35b3ecbbed196a344ed6b5c7ee6f50faf9b7eee836044d1c7ffe10093ef45
  Gas price: 0.0 gwei   Gas limit: 6721975
  Flashloan.constructor confirmed - Block: 9995378   Gas used: 796934 (11.86%)
  Flashloan deployed at: 0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87
```

4. Approve the strategy for the Vault. We must do this because we only approved Strategies can pull funding from the Vault.

```python
# 1000 DAI debt limit, no rate limit, 50 bps strategist fee
>>> vault.addStrategy(strategy, Wei("1000 ether"), 2 ** 256 - 1, 50, {"from": gov})
Transaction sent: 0xa70b90eb9a9899e8f6e709c53a436976315b4279c4b6797d0a293e169f94d5b4
  Gas price: 0.0 gwei   Gas limit: 6721975
  Transaction confirmed - Block: 9995379   Gas used: 21055 (0.31%)
```

5. Now we are ready to put our strategy into action!

```python
>>> harvest_tx = strategy.harvest({"from": accounts[0]})  # perform as many time as desired...
```

## Implementing Strategy Logic

[`contracts/Strategy.sol`](contracts/Strategy.sol) is where you implement your own logic for your strategy. In particular:

* Create a descriptive name for your strategy via `Strategy.name()`.
* Invest your want tokens via `Strategy.adjustPosition()`.
* Take profits and report losses via `Strategy.prepareReturn()`.
* Unwind enough of your position to payback withdrawals via `Strategy.liquidatePosition()`.
* Unwind all of your positions via `Strategy.exitPosition()`.
* Fill in a way to estimate the total `want` tokens managed by the strategy via `Strategy.estimatedTotalAssets()`.
* Migrate all the positions managed by your strategy via `Strategy.prepareMigration()`.
* Make a list of all position tokens that should be protected against movements via `Strategy.protectedTokens()`.

## Testing

To run the tests:

```
brownie test
```

The example tests provided in this mix start by deploying and approving your [`Strategy.sol`](contracts/Strategy.sol) contract. This ensures that the loan executes succesfully without any custom logic. Once you have built your own logic, you should edit [`tests/test_flashloan.py`](tests/test_flashloan.py) and remove this initial funding logic.

See the [Brownie documentation](https://eth-brownie.readthedocs.io/en/stable/tests-pytest-intro.html) for more detailed information on testing your project.

## Debugging Failed Transactions

Use the `--interactive` flag to open a console immediatly after each failing test:

```
brownie test --interactive
```

Within the console, transaction data is available in the [`history`](https://eth-brownie.readthedocs.io/en/stable/api-network.html#txhistory) container:

```python
>>> history
[<Transaction '0x50f41e2a3c3f44e5d57ae294a8f872f7b97de0cb79b2a4f43cf9f2b6bac61fb4'>,
 <Transaction '0xb05a87885790b579982983e7079d811c1e269b2c678d99ecb0a3a5104a666138'>]
```

Examine the [`TransactionReceipt`](https://eth-brownie.readthedocs.io/en/stable/api-network.html#transactionreceipt) for the failed test to determine what went wrong. For example, to view a traceback:

```python
>>> tx = history[-1]
>>> tx.traceback()
```

To view a tree map of how the transaction executed:

```python
>>> tx.call_trace()
```

See the [Brownie documentation](https://eth-brownie.readthedocs.io/en/stable/core-transactions.html) for more detailed information on debugging failed transactions.


## Deployment

When you are finished testing and ready to deploy to the mainnet:

1. [Import a keystore](https://eth-brownie.readthedocs.io/en/stable/account-management.html#importing-from-a-private-key) into Brownie for the account you wish to deploy from.
2. Edit [`scripts/deployment.py`](scripts/deployment.py) and add your keystore ID according to the comments.
3. Run the deployment script on the mainnet using the following command:

```bash
$ brownie run deployment --network mainnet
```

You will be prompted to enter your keystore password, and then the contract will be deployed.





## WIP Demo Deployments

Strategy Upgradeable Proxy (wBTC / ibBTC Vault)
0x7FD16fa571ec3118Dd1323b75A037Ed2fcC2cbf5

Strategy Logic
0x0Ab7aEc23C0224fE48FfC976bbb8E6f461bff81b