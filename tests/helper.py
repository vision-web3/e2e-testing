import glob
import os
import pathlib
import subprocess
import requests
import time
import dotenv
import pantos.client.library.configuration as pc_conf
import concurrent.futures


def wait_for_service_node_to_be_ready():
    max_tries = 100
    while True:
        max_tries -= 1
        if max_tries == 0:
            raise TimeoutError('Service node did not start in time')
        try:
            response = requests.get('http://localhost:8081/bids?source_blockchain=0&destination_blockchain=1', timeout=60)
        except requests.exceptions.ConnectionError:
            print('Service node not ready yet')
            time.sleep(5)
            continue
        # response.raise_for_status()
        print(response.status_code)
        bids = response.json()
        if len(bids) > 0:
            print('Service node is ready')
            break
        time.sleep(5)


def teardown_environment(stack_id = ''):
    configure_nodes({}, stack_id)    

def run_command(command, cwd, env_vars):
    # Merge environment variables
    env = {**os.environ, **env_vars}

    print(f'Running command: {command} in {cwd} with environment: {env_vars}')
    process = subprocess.Popen(command, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, bufsize=0)
    for line in process.stdout:
        print(line.decode(), end='')
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command)

def configure_nodes(config, stack_id):
    pantos_ethereum_contracts_dir = os.getenv('PANTOS_ETHEREUM_CONTRACTS')
    pantos_ethereum_contracts_version = os.getenv('PANTOS_ETHEREUM_CONTRACTS_VERSION', 'development')
    if not pantos_ethereum_contracts_version or pantos_ethereum_contracts_version == '':
        pantos_ethereum_contracts_version = 'development'
    pantos_service_node_dir = os.getenv('PANTOS_SERVICE_NODE')
    pantos_service_node_version = os.getenv('PANTOS_SERVICE_NODE_VERSION', 'development')
    if not pantos_service_node_version or pantos_service_node_version == '':
        pantos_service_node_version = 'development'
    pantos_validator_node_dir = os.getenv('PANTOS_VALIDATOR_NODE')
    pantos_validator_node_version = os.getenv('PANTOS_VALIDATOR_NODE_VERSION', 'development')
    if not pantos_validator_node_version or pantos_validator_node_version == '':
        pantos_validator_node_version = 'development'

    if not pantos_ethereum_contracts_dir:
        raise EnvironmentError('PANTOS_ETHEREUM_CONTRACTS environment variable not set')

    print(f'Configuring tests with: Ethereum Contracts {pantos_ethereum_contracts_version}, Service Node {pantos_service_node_version}, Validator Node {pantos_validator_node_version}')

    # Teardown
    if not config:
        print('Tearing down the environment')
        # Dump all the logs
        env_vars = {'STACK_IDENTIFIER': stack_id}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(run_command, 'docker ps', None, {}),
                executor.submit(run_command, 'make docker-logs', pantos_validator_node_dir, env_vars),
                executor.submit(run_command, 'make docker-logs', pantos_service_node_dir, env_vars),
                executor.submit(run_command, 'make docker-logs', pantos_ethereum_contracts_dir, env_vars)
            ]
            concurrent.futures.wait(futures)

        # Remove the containers
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(run_command, 'make docker-remove', pantos_validator_node_dir, env_vars),
                executor.submit(run_command, 'make docker-remove', pantos_service_node_dir, env_vars),
                executor.submit(run_command, 'make docker-remove', pantos_ethereum_contracts_dir, env_vars)
            ]
            concurrent.futures.wait(futures)

        return

    # Configure Ethereum contracts
    if 'ethereum_contracts' in config:
        ethereum_contracts_command = 'make docker-local'
        ethereum_contracts_env_vars = {'DOCKER_TAG': pantos_ethereum_contracts_version, 'STACK_IDENTIFIER': stack_id, 'ARGS': '--no-build'}
    else:
        ethereum_contracts_command = 'make docker-remove'
        ethereum_contracts_env_vars = {'STACK_IDENTIFIER': stack_id}
    run_command(ethereum_contracts_command, pantos_ethereum_contracts_dir, ethereum_contracts_env_vars)

    # Configure Service Node
    if 'service_node' in config:
        instance_count = config['service_node'].get('instance_count', 1)
        service_node_command = f'make docker INSTANCE_COUNT="{instance_count}"'
        # TODO: Allow service nodes to support multiple networks?
        service_node_env_vars = {'DOCKER_TAG': pantos_service_node_version, 'STACK_IDENTIFIER': stack_id, 'ETHEREUM_NETWORK': '1', 'NO_BUILD': 'true'}
    else:
        service_node_command = 'make docker-remove'
        service_node_env_vars = {'STACK_IDENTIFIER': stack_id}

    # Configure Validator Node
    if 'validator_node' in config:
        instance_count = config['validator_node'].get('instance_count', 1)
        validator_node_command = f'make docker INSTANCE_COUNT="{instance_count}"'
        validator_node_env_vars = {'DOCKER_TAG': pantos_validator_node_version, 'STACK_IDENTIFIER': stack_id, 'ETHEREUM_NETWORK': '1', 'NO_BUILD': 'true'}
    else:
        validator_node_command = 'make docker-remove'
        validator_node_env_vars = {'STACK_IDENTIFIER': stack_id}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(run_command, service_node_command, pantos_service_node_dir, service_node_env_vars),
            executor.submit(run_command, validator_node_command, pantos_validator_node_dir, validator_node_env_vars),
        ]
        concurrent.futures.wait(futures)


def configure_client(stack_id, instance=1):
    if not os.getenv('PANTOS_ETHEREUM_CONTRACTS'):
        raise EnvironmentError('PANTOS_ETHEREUM_CONTRACTS environment variable not set')
    contracts_dir = os.getenv('PANTOS_ETHEREUM_CONTRACTS')
    current_dir = os.path.dirname(os.path.realpath(__file__))

    # TODO: Return one library instance per instance from the stack id
    for file in [f'{contracts_dir}/data/*{stack_id}-{instance}/*/all.env', f'{current_dir}/../base.env']:
        resolved_path = glob.glob(file)
        if not resolved_path:
            raise FileNotFoundError(f'Environment path {file} not found')
        for env_file in resolved_path:
            if not pathlib.Path(env_file).exists():
                raise FileNotFoundError(f'Environment file {env_file} not found')
            dotenv.load_dotenv(env_file)

    pc_conf.load_config(None, True)
