# e2e-testing

A collection of functionalities to test Vision deployments end-to-end (E2E).

## Prerequisites

Ensure you have Poetry installed. Then, run the following command:

```shell
poetry install
```

Next, make a copy of example.env as .env. Fill in the paths of the dependent projects. You can use the officially built images or alternatively, use locally deployed images.

## How to Run Local Tests

To run all the tests, use the following command:

```shell
make test
```

## How to Check an Environment

You can run the tests in environment-check mode by defining the following variables:

```shell
VISION_ENV_FILE=<path to the configuration file>
<CHAIN>_PRIVATE_KEY=<either a valid path or the value of the keystore>
<CHAIN>_RECEIVING_ADDRESS=<receiving address for the tests on a specific chain, e.g., ETHEREUM>
```

Once these variables are defined, you can run the tests with:

```shell
make test
```
