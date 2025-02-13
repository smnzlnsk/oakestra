import requests
import threading
import os
import service_operations
import traceback

from mongodb_client import mongo_aggregate_node_information, mongo_get_services_with_failed_instanes
from my_prometheus_client import prometheus_set_metrics

SYSTEM_MANAGER_ADDR = 'http://' + os.environ.get('SYSTEM_MANAGER_URL') + ':' + os.environ.get('SYSTEM_MANAGER_PORT')
SYSTEM_MANAGER_ADDR_v6 = 'http://' + os.environ.get('SYSTEM_MANAGER_URL_v6') + ':' + os.environ.get('SYSTEM_MANAGER_PORT')

def send_aggregated_info_to_sm(my_id, time_interval):
    try:
        data = mongo_aggregate_node_information(time_interval)
        threading.Thread(group=None, target=send_aggregated_info,
                         args=(my_id, data)).start()
        prometheus_set_metrics(my_id=my_id, data=data)
    except Exception as e:
        print(e)
        traceback.print_exc()


def re_deploy_dead_services_routine():
    re_deploy_triggers = ['FAILED', 'DEAD', 'NO_WORKER_CAPACITY']
    try:
        services = mongo_get_services_with_failed_instanes()
        if services is not None:
            for service in services:
                for instance in service.get("instance_list", []):
                    if instance.get('status', '') in re_deploy_triggers:
                        print('FAILED INSTANCE, ATTEMPTING RE-DEPLOY')
                        threading.Thread(group=None, target=trigger_undeploy_and_re_deploy,
                                         args=(service, instance)).start()
    except Exception as e:
        print(e)
        traceback.print_exc()


def send_aggregated_info(my_id, data):
    # TODO re-enable
    #print('Sending aggregated information to System Manager.')
    #print(SYSTEM_MANAGER_ADDR_v6)
    try:
        requests.post(SYSTEM_MANAGER_ADDR_v6 + '/api/information/' + str(my_id), json=data)
    except requests.exceptions.RequestException as e:
        print('Calling System Manager /api/information not successful.')
        print(e)


def trigger_undeploy_and_re_deploy(service, instance):
    try:
        service_operations.delete_service(service.get('system_job_id'), instance.get('instance_number'))
        service_operations.deploy_service(service, str(service.get('system_job_id')),
                                          str(instance.get('instance_number')))
    except Exception as e:
        print(e)


def cloud_request_incr_node(my_id):
    print('reporting to cloud about new worker node...')
    request_addr = SYSTEM_MANAGER_ADDR_v6 + '/api/cluster/' + str(my_id) + '/incr_node'
    print(request_addr)
    try:
        requests.get(request_addr)
    except requests.exceptions.RequestException as e:
        print('Calling System Manager /api/cluster/../incr_node not successful.')
