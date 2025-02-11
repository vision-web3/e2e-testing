import decimal
import os
import sys
import time
import pytest
import pantos.client as pc
from pantos.client.library.entitites import DestinationTransferStatus
from pantos.common.servicenodes import ServiceNodeTransferStatus

from helper import configure_client, configure_nodes, teardown_environment
from conftest import configure_existing_environment

test_timeout = int(os.getenv('PYTEST_TIMEOUT', 300))  # 5 minutes

@pytest.fixture(scope="module", autouse=True)
def setup_module(request, stack_id, worker_id = "gw0"):
    # Code to set up the environment before any tests in the module
    print("Setting up module environment")
    #os.environ['PANTOS_ENV_FILE'] = '/Users/joe.matthew/Workspace/cd-workflows/tests/testnet/e2e-test-config.env'
    #os.environ['ETHEREUM_PRIVATE_KEY'] = '{"address":"f5454fd5b6aac3d243226cec31489c507a8259e0","crypto":{"cipher":"aes-128-ctr","ciphertext":"65a77c0acf155567086e1f231194ac13556e1148aa5b2170f509c679ccc8d68f","cipherparams":{"iv":"aa61677cf5316fcf7f514bc8db8d6528"},"kdf":"scrypt","kdfparams":{"dklen":32,"n":262144,"p":1,"r":8,"salt":"cc9be3fe948e1c46cee2a86082c4db868c3f86fe4b4953f56c2c2624675e9d2e"},"mac":"7f73f4aeda2025086eb608ab360ca5b763d846aec2c331be069e42676ba25241"},"id":"712ce8d5-0ed5-4d32-83a4-0d9b1fa8a290","version":3}'
    #os.environ['BNB_CHAIN_PRIVATE_KEY'] = '/Users/joe.matthew/Workspace/e2e-testing/keystore'
    if os.getenv('PANTOS_ENV_FILE', None) is None:
        port_offset = int(worker_id.replace("gw", "")) if worker_id != "master" else 0
        #os.environ['PORT_OFFSET'] = str(port_offset)
        configure_nodes({
            'ethereum_contracts': {'args': '', 'port_group': port_offset},
            'service_node': {'instance_count': 1, 'port_group': port_offset},
            'validator_node': {'instance_count': 1, 'port_group': port_offset}
        }, stack_id)
        configure_client(stack_id)
        request.addfinalizer(lambda: teardown_environment(stack_id))
    else:
        # Used to check an existing deployment
        configure_existing_environment()
        import subprocess
        print(subprocess.call(['docker', 'ps']))

@pytest.mark.parametrize('receiving_address', ['bnb'], indirect=True)
def test_retrieve_token_balance(receiving_address):
    try:
        token_balance = pc.retrieve_token_balance(
            pc.Blockchain.ETHEREUM,
            pc.BlockchainAddress(receiving_address),
            pc.TokenSymbol('pan'))
        assert token_balance is not None
        print(f'Token balance: {token_balance}')
    except pc.PantosClientError:
        pytest.fail("PantosClientError raised")

def test_retrieve_service_node_bids():
    try:
        service_node_bids = pc.retrieve_service_node_bids(pc.Blockchain.ETHEREUM,
                                                          pc.Blockchain.BNB_CHAIN, False)
        assert service_node_bids != {}
        print(f'Service node bids: {service_node_bids}')
    except pc.PantosClientError:
        pytest.fail("PantosClientError raised")

@pytest.mark.timeout(test_timeout)
@pytest.mark.parametrize('keystore', ['eth'], indirect=True)
@pytest.mark.parametrize('receiving_address', ['bnb'], indirect=True)
def test_token_transfer(receiving_address, private_key):
    try:
        token_transfer_response = pc.transfer_tokens(
            pc.Blockchain.ETHEREUM, pc.Blockchain.BNB_CHAIN, private_key,
            pc.BlockchainAddress(receiving_address),
            pc.TokenSymbol('pan'), decimal.Decimal('0.000001'))
        assert token_transfer_response is not None
        print(f'Token transfer response: {token_transfer_response}')
    except pc.PantosClientError:
        pytest.fail("PantosClientError raised")

    done = False
    while not done:
        try:
            token_transfer_status = pc.get_token_transfer_status(
                pc.Blockchain.ETHEREUM, token_transfer_response.service_node_address,
                token_transfer_response.task_id)
            assert token_transfer_status is not None
            print(f'Token transfer status: {token_transfer_status}')
            if (token_transfer_status.source_transfer_status is ServiceNodeTransferStatus.CONFIRMED
                and token_transfer_status.destination_transfer_status is DestinationTransferStatus.CONFIRMED):
                done = True
            else:
                print('Waiting for transfer to be confirmed...')
                time.sleep(5)
        except pc.PantosClientError:
            pytest.fail("PantosClientError raised")

# Enable when we can start the token creator
# @pytest.mark.parametrize('keystore', ['eth'], indirect=True)
# def test_deploy_pantos_compatible_token(private_key):
#     try:
#         deployment_blockchains = [pc.Blockchain.ETHEREUM]
#         payment_blockchain = pc.Blockchain.ETHEREUM
#         task_id = pc.deploy_pantos_compatible_token('Test_cli', 'TCLI', 7, True,
#                                                     False, 54321,
#                                                     deployment_blockchains,
#                                                     payment_blockchain,
#                                                     private_key)
#         assert task_id is not None
#         print(f'Task ID deployment: {task_id}')
#     except pc.PantosClientError:
#         pytest.fail("PantosClientError raised")    
