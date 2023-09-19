import requests
import os


SERVICE_MANAGER_ADDR = 'http://' + os.environ.get('CLUSTER_SERVICE_MANAGER_ADDR') + ':' + os.environ.get(
    'CLUSTER_SERVICE_MANAGER_PORT')


def network_notify_deployment(job_id, job):
    print('Sending network deployment notification to the network component')
    job["_id"] = str(job["_id"])
    try:
        requests.post(SERVICE_MANAGER_ADDR + '/api/net/deployment', json={'job_name': job['job_name']})
    except requests.exceptions.RequestException as e:
        print('Calling Service Manager /api/net/deployment not successful.')


def network_notify_migration(job_id, job):
    pass


def network_notify_undeployment(job_id, job):
    pass


def network_notify_gateway_deploy(gateway_info):
    print('Sending netmanager registration information to the network component')    
    try:
        requests.post(SERVICE_MANAGER_ADDR + '/api/net/gateway/deploy', json=gateway_info)
    except requests.exceptions.RequestException as e:
        print('Calling Service Manager /api/net/gateway/deploy not successul')
