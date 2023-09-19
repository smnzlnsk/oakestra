import logging
import os
import requests
import time

# net_plugin = root_service_manager
NET_PLUGIN_ADDR = 'http://' + os.environ.get('NET_PLUGIN_URL', 'localhost') + ':' + str(
    os.environ.get('NET_PLUGIN_PORT', '10010'))


def net_inform_service_deploy(job, job_id):
    """
    Inform the network plugin about the deploy
    """
    logging.debug('new job: communicating service deploy to network plugin...')
    logging.debug(job)
    request_addr = NET_PLUGIN_ADDR + '/api/net/service/deploy'
    logging.debug(request_addr)

    job['_id'] = str(job_id)
    job['system_job_id'] = str(job_id)
    r = requests.post(request_addr, json={'deployment_descriptor': job, 'system_job_id': job_id})
    r.raise_for_status()


def net_inform_service_undeploy(job_id):
    """
    Inform the network plugin about the deploy
    """
    logging.debug('delete job: communicating service undeploy to network plugin...')
    request_addr = NET_PLUGIN_ADDR + '/api/net/service/' + str(job_id)
    logging.debug(request_addr)

    try:
        r = requests.delete(request_addr)
        r.raise_for_status()
    except requests.exceptions.ConnectionError as errc:
        logging.error('Calling network plugin ' + request_addr + ' Connection error.')
    except requests.exceptions.Timeout as errt:
        logging.error('Calling network plugin ' + request_addr + ' Timeout error.')
    except requests.exceptions.RequestException as err:
        logging.error('Calling network plugin ' + request_addr + ' Request Exception.')


def net_inform_instance_deploy(job_id, instance_number, cluster_id):
    """
    Inform the network plugin about the new service's instance scheduled
    """
    logging.debug('new job: communicating instance deploy to network plugin...')
    request_addr = NET_PLUGIN_ADDR + '/api/net/instance/deploy'
    logging.debug(request_addr)

    r = requests.post(request_addr,
                      json={'instance_number': instance_number, 'cluster_id': cluster_id, 'system_job_id': job_id})
    r.raise_for_status()


def net_inform_instance_undeploy(job_id, instance):
    """
    Inform the network plugin about an undeployed instance
    """
    logging.debug('new job: communicating instance undeploy to network plugin...')
    request_addr = NET_PLUGIN_ADDR + '/api/net/' + str(job_id) + '/' + str(instance)
    logging.debug(request_addr)
    try:
        r = requests.delete(request_addr)
        r.raise_for_status()
    except requests.exceptions.ConnectionError as errc:
        logging.error('Calling network plugin ' + request_addr + ' Connection error.')
    except requests.exceptions.Timeout as errt:
        logging.error('Calling network plugin ' + request_addr + ' Timeout error.')
    except requests.exceptions.RequestException as err:
        logging.error('Calling network plugin ' + request_addr + ' Request Exception.')


def net_register_cluster(cluster_id, cluster_address, cluster_port):
    """
    Inform the network plugin about the new registered cluster
    """
    logging.debug('new job: communicating cluster registration to net component...')
    request_addr = NET_PLUGIN_ADDR + '/api/net/cluster'
    try:
        r = requests.post(request_addr,
                          json={
                              'cluster_id': cluster_id,
                              'cluster_address': cluster_address,
                              'cluster_port': cluster_port
                          })
        logging.debug(r)
        r.raise_for_status()
    except requests.exceptions.ConnectionError as errc:
        logging.error('Calling network plugin ' + request_addr + ' Connection error.')
    except requests.exceptions.Timeout as errt:
        logging.error('Calling network plugin ' + request_addr + ' Timeout error.')
    except requests.exceptions.RequestException as err:
        logging.error('Calling network plugin ' + request_addr + ' Request Exception.')


def net_inform_gateway_deploy(gateway):
    """
    Inform the network plugin about the gateway component to deploy on a node
    """
    logging.debug('new job: communicating gateway deployment to net component...')
    request_addr = NET_PLUGIN_ADDR + '/api/gateway/deploy'
    try:
        r = requests.post(request_addr,
                          json=gateway)
        logging.debug(r)
        r.raise_for_status()
    except requests.exceptions.ConnectionError as errc:
        logging.error('Calling network plugin ' + request_addr + ' Connection error.')
    except requests.exceptions.Timeout as errt:
        logging.error('Calling network plugin ' + request_addr + ' Timeout error.')
    except requests.exceptions.RequestException as err:
        logging.error('Calling network plugin ' + request_addr + ' Request Exception.')
    return


def net_inform_gateway_undeploy(gateway_id):
    """
    Inform the network plugin about an undeployed gateway
    """
    logging.debug('new job: communicating gateway undeploy to network plugin...')
    request_addr = NET_PLUGIN_ADDR + '/api/gateway/undeploy/' + str(gateway_id)
    logging.debug(request_addr)
    try:
        r = requests.delete(request_addr)
        r.raise_for_status()
    except requests.exceptions.ConnectionError as errc:
        logging.error('Calling network plugin ' + request_addr + ' Connection error.')
    except requests.exceptions.Timeout as errt:
        logging.error('Calling network plugin ' + request_addr + ' Timeout error.')
    except requests.exceptions.RequestException as err:
        logging.error('Calling network plugin ' + request_addr + ' Request Exception.')
    return


def net_inform_firewall_deploy(component_desc):
    """
    Inform the network plugin about the firewall component to deploy on a node
    """
    logging.debug('new job: communicating firewall deployment to net component...')
    request_addr = NET_PLUGIN_ADDR + '/api/firewall/deploy'
    try:
        r = requests.post(request_addr,
                          json=component_desc)
        logging.debug(r)
        r.raise_for_status()
    except requests.exceptions.ConnectionError as errc:
        logging.error('Calling network plugin ' + request_addr + ' Connection error.')
    except requests.exceptions.Timeout as errt:
        logging.error('Calling network plugin ' + request_addr + ' Timeout error.')
    except requests.exceptions.RequestException as err:
        logging.error('Calling network plugin ' + request_addr + ' Request Exception.')


def net_inform_firewall_update(node_id):
    # TODO
    return


def net_inform_firewall_undeploy(firewall_id):
    """
    Inform the network plugin about an undeployed firewall
    """
    logging.debug('new job: communicating firewall undeploy to network plugin...')
    request_addr = NET_PLUGIN_ADDR + '/api/gateway/component/' + str(firewall_id)
    logging.debug(request_addr)
    try:
        r = requests.delete(request_addr)
        r.raise_for_status()
    except requests.exceptions.ConnectionError as errc:
        logging.error('Calling network plugin ' + request_addr + ' Connection error.')
    except requests.exceptions.Timeout as errt:
        logging.error('Calling network plugin ' + request_addr + ' Timeout error.')
    except requests.exceptions.RequestException as err:
        logging.error('Calling network plugin ' + request_addr + ' Request Exception.')
