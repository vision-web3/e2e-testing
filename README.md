# e2e-testing

A collection of functionalities to test Pantos deployments end-to-end (E2E).

## Prerequisites

Ensure you have Poetry installed. Then, run the following command:

```shell
poetry install
```

Next, make a copy of example.env as .env. Fill in the paths of the dependent projects. You can use the officially built images or alternatively, use locally deployed images.

## How to run

To run all the tests, use the following command:

```shell
make test
```
