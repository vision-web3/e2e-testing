import glob
import os
import pathlib
import random
import string
import sys
import dotenv
import pytest
import pantos.client as pc

if os.getenv('DEBUG', 'false').lower() == 'true':
    sys.stdout = sys.stderr

if pathlib.Path('.env').exists():
    dotenv.load_dotenv('.env')

@pytest.fixture
def receiving_address():
    return '0xaAE34Ec313A97265635B8496468928549cdd4AB7'

def generate_random_string(length=5):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

@pytest.fixture(scope='module')
def stack_id():
    return generate_random_string()

@pytest.fixture
def keystore(request, stack_id):
    network = request.param if request and request.param else 'eth'
    contracts_dir = os.getenv('PANTOS_ETHEREUM_CONTRACTS')
    file = f'{contracts_dir}/data/*{stack_id}-1/{network}/keystore'
    resolved_path = glob.glob(file)
    if not resolved_path:
        raise FileNotFoundError(f'Environment path {file} not found')
    if len(resolved_path) > 1:
        raise FileNotFoundError(f'Multiple keystore files found: {resolved_path}')
    with open(resolved_path[0], 'r') as keystore_file:
        keystore = keystore_file.read()
    return keystore

@pytest.fixture
def private_key(keystore):
    # Decrypt private key
    private_key = pc.decrypt_private_key(pc.Blockchain.ETHEREUM, keystore, '')
    return private_key
