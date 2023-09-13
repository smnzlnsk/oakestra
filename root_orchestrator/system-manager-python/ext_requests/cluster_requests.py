import logging
import time
import requests

from ext_requests.apps_db import mongo_find_job_by_id, mongo_find_cluster_of_job
from ext_requests.cluster_db import mongo_find_cluster_by_id, mongo_find_cluster_by_ip
from ext_requests.gateway_db import mongo_find_gateway_by_id

def cluster_request_to_deploy(cluster_id, job_id, instance_number):
    print('propagate to cluster...')
    cluster = mongo_find_cluster_by_id(cluster_id)
    job = mongo_find_job_by_id(job_id)
    # adjusted cluster_addr for ipv6
    try:
        cluster_addr = 'http://[' + cluster.get('ip') + ']:' + str(cluster.get('port')) + '/api/deploy/' + str(job_id) + "/" + str(instance_number)
        job['_id'] = str(job['_id'])
        resp = requests.post(cluster_addr, json=job)
        print(resp)
    except requests.exceptions.RequestException as e:
        print('Calling Cluster Orchestrator /api/deploy not successful.')


def cluster_request_to_delete_job(job_id, instance_number):
    cluster = mongo_find_cluster_of_job(job_id, int(instance_number))
    try:
        cluster_addr = 'http://[' + cluster.get('ip') + ']:' + str(cluster.get('port')) + '/api/delete/' + str(
            job_id) + "/" + str(instance_number)
        resp = requests.get(cluster_addr)
        print(resp)
    except Exception as e:
        logging.error(e)
        print(e)
        print('Calling Cluster Orchestrator /api/delete not successful.')


def cluster_request_to_delete_job_by_ip(job_id, instance_number,ip):
    try:
        cluster = mongo_find_cluster_by_ip(ip)
        cluster_addr = 'http://[' + cluster.get('ip') + ']:' + str(cluster.get('port')) + '/api/delete/' + str(
            job_id) + "/" + str(instance_number)
        resp = requests.get(cluster_addr)
        print(resp)
    except Exception as e:
        logging.error(e)
        print('Calling Cluster Orchestrator /api/delete not successful.')


def cluster_request_to_replicate_up(cluster_obj, job_obj, int_replicas):
    cluster_addr = 'http://[' + cluster_obj.get('ip') + ']:' + str(cluster_obj.get('port')) + '/api/replicate/'
    try:
        resp = requests.post(cluster_addr, json={'job': job_obj, 'int_replicas': int_replicas})
        print(resp)
        return 1
    except requests.exceptions.RequestException as e:
        print('Calling Cluster Orchestrator /api/replicate not successful.')


def cluster_request_to_replicate_down(cluster_obj, job_obj, int_replicas):
    cluster_addr = 'http://[' + cluster_obj.get('ip') + ']:' + str(cluster_obj.get('port')) + '/api/replicate/'
    try:
        resp = requests.post(cluster_addr, json={'job': job_obj, 'int_replicas': int_replicas})
        print(resp)
        return 1
    except requests.exceptions.RequestException as e:
        print('Calling Cluster Orchestrator /api/replicate not successful.')


def cluster_request_to_move_within_cluster(cluster_obj, job_id, node_from, node_to):
    cluster_addr = 'http://[' + cluster_obj.get('ip') + ']:' + str(cluster_obj.get('port')) + '/api/move/'
    try:
        resp = requests.post(cluster_addr, json={'job': job_id, 'node_from': node_from, 'node_to': node_to})
        print(resp)
        return 1
    except requests.exceptions.RequestException as e:
        print('Calling Cluster Orchestrator /api/move not successful.')


def cluster_request_to_deploy_gateway(cluster_id, microservice):
    print('propagate to cluster...')
    cluster = mongo_find_cluster_by_id(cluster_id)
    #gateway = mongo_find_gateway_by_id(gateway_id)
    json_data = microservice
    print(json_data)

    # adjusted cluster_addr for ipv6
    try:
        cluster_addr = 'http://[' + cluster.get('ip') + ']:' + str(cluster.get('port')) + '/api/gateway/deploy'
        #gateway['_id'] = str(gateway['_id'])
        resp = requests.post(cluster_addr, json=json_data)
        print(resp)
    except requests.exceptions.RequestException as e:
        print('Calling Cluster Orchestrator /api/gateway/deploy not successful.')


def cluster_request_to_update_gateway(cluster_id, gateway_id, microservice):
    print('propagate to cluster...')
    cluster = mongo_find_cluster_by_id(cluster_id)
    gateway = mongo_find_gateway_by_id(gateway_id)
    # adjusted cluster_addr for ipv6
    try:
        cluster_addr = 'http://[' + cluster.get('ip') + ']:' + str(cluster.get('port')) + '/api/gateway/update/' + str(gateway_id)
        gateway['_id'] = str(gateway['_id'])
        resp = requests.post(cluster_addr, json=microservice)
        print(resp)
    except requests.exceptions.RequestException as e:
        print('Calling Cluster Orchestrator /api/gateway/update not successful.')