import glob
import os
import pathlib
import random
import string
import sys
import dotenv
import pytest
import pantos.client as pc
import pantos.client.library.configuration as pc_conf

if os.getenv('DEBUG', 'false').lower() == 'true':
    sys.stdout = sys.stderr

if pathlib.Path('.env').exists():
    dotenv.load_dotenv('.env')

existing_env_check = False

@pytest.fixture
def receiving_address(request):
    global existing_env_check
    global env_mapping
    network = request.param if request and request.param else 'eth'
    if existing_env_check:
        address = os.getenv(f'{env_mapping[network].upper()}_RECEIVING_ADDRESS', None)
        if not address:
            raise EnvironmentError(f'{env_mapping[network].upper()} environment variable not set')
        return address
    return '0xaAE34Ec313A97265635B8496468928549cdd4AB7'

def generate_random_string(length=5):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

@pytest.fixture(scope='module')
def stack_id():
    return generate_random_string()

# Temporary until we can fix the naming scheme in the configuration
env_mapping = {
    'eth': 'ethereum',
    'bnb': 'bnb',
}

chain_mapping = {
    'eth': pc.Blockchain.ETHEREUM,
    'bnb': pc.Blockchain.BNB_CHAIN,
}

@pytest.fixture
def keystore(request, stack_id):
    global existing_env_check
    network = request.param if request and request.param else 'eth'
    if existing_env_check:
        global env_mapping
        private_key_name = f'{env_mapping[network].upper()}_PRIVATE_KEY'
        resolved_path = os.getenv(private_key_name, None)
        if not resolved_path:
            raise EnvironmentError(f'Environment keystore for network {network} not found, used {private_key_name}')
        try:
            with open(resolved_path, 'r') as keystore_file:
                keystore = keystore_file.read()
            return (keystore, network)
        except:
            # Assume it's the keystore on its own
            return (resolved_path, network)

    contracts_dir = os.getenv('PANTOS_ETHEREUM_CONTRACTS')
    file = f'{contracts_dir}/data/*{stack_id}-1/{network}/keystore'
    resolved_path = glob.glob(file)
    if not resolved_path:
        raise FileNotFoundError(f'Environment path {file} not found')
    if len(resolved_path) > 1:
        raise FileNotFoundError(f'Multiple keystore files found: {resolved_path}')
    with open(resolved_path[0], 'r') as keystore_file:
        keystore = keystore_file.read()
    return (keystore, network)

@pytest.fixture
def private_key(keystore):
    # Decrypt private key
    global chain_mapping
    private_key = pc.decrypt_private_key(chain_mapping[keystore[1]], keystore[0], '')
    return private_key
    
def configure_existing_environment():
    global existing_env_check
    if not os.getenv('PANTOS_ENV_FILE'):
        raise EnvironmentError('PANTOS_ENV_FILE environment variable not set')
    file = os.getenv('PANTOS_ENV_FILE')
    if not pathlib.Path(file).exists():
        raise FileNotFoundError(f'Environment file {file} not found')
    
    dotenv.load_dotenv(file)
    
    pc_conf.load_config(None, True)
    
    existing_env_check = True
