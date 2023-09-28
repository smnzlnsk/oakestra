import ipaddress
from gateway_db import *
from bson import ObjectId
from mqtt_client import mqtt_publish_firewall_deploy, mqtt_publish_new_firewall_rule
from network_plugin_requests import network_notify_gateway_deploy

def deploy_gateway(service):
    """
    Decision making on whether a gateway or firewall is needed for instances of service
    @param service: service data to expose
    @return message and http code
    """

    port_already_in_use = mongo_get_service_by_exposed_port(service['exposed_port'])
    if port_already_in_use is not None:
        return {'message': 'port already in use'}, 500
    
    # add service to collection of exposed services
    gateway_service = mongo_add_gateway_service(service)

    # get distinct set of nodes of running instances
    workers = mongo_get_service_instance_node_information(service['microserviceID'])
    # instances = worker_information['instance_list']
    for worker in workers:
        # check if worker instance IP is part of oakestra network
        """
        if _is_public_IP(instance['publicip']):
            # check if worker already has running firewall
            node = mongo_get_gateway_node(instance['worker_id'])
            if node is None:
                # publicly addressable worker node does not have a firewall deployed
                # so deploy one and
                deploy_firewall_process_on_worker(instance)
            # update its firewall rules
            update_firewall_rules_on_worker(instance['worker_id'], service)
        else:
        """
            # get a gateway, able to expose the requested service
        
        gateway = mongo_find_available_gateway_by_port(service['exposed_port'])
        print('mongo_find_available_gateway_by_port: ', gateway)
        if gateway is None:
            # if no gateway available, deploy a new one
            gateway = deploy_gateway_process_on_cluster()
            print('deploy gateway process: ', gateway)
            # if deployment impossible, return 500
            if gateway is None:
                mongo_delete_gateway_service(service_id=service['microserviceID'])
                return {'message': 'service exposal impossible'}, 500
            # update its firewall rules
        print('updating firewall')
        update_gateway_service_exposal(gateway['gateway_id'], service)
        print('firewall updated')
    gateways = mongo_get_gateways_of_service(service['microserviceID'])
    print('got gateways deployed: ', gateways)
    return {'message': gateways}, 200


def deploy_firewall_process_on_worker(worker_info):
    gateway_info = prepare_gateway_node_entry(worker_info, 'firewall')
    firewall_id = mongo_add_gateway_node(gateway_info)
    mqtt_publish_firewall_deploy(gateway_info['worker_id'], firewall_id)
    return gateway_info


def update_firewall_rules_on_worker(worker_id, service):
    service_info = prepare_gateway_node_service_entry(service)
    mongo_add_gateway_service_to_node(worker_id, service_info)
    mqtt_publish_new_firewall_rule(worker_id, service_info)
    return


def deploy_gateway_process_on_cluster():
    # find idle netmanager
    worker_info = mongo_find_available_idle_worker()
    print('idle netmanager: ', worker_info)
    gateway_info = prepare_gateway_node_entry(worker_info, 'gateway')
    print('gateway_info: ', gateway_info)
    # remove netmanager entry from table of netmanagers and add to active gateways
    gateway_id = mongo_add_gateway_node(gateway_info)
    print('gateway_info after swapping it, before sending it to network component, also being returned: ', gateway_info)
    # notify cluster service-manager
    gateway_info['_id'] = str(gateway_info['_id'])
    network_notify_gateway_deploy(gateway_info)
    return gateway_info


def update_gateway_service_exposal(gateway_id, service):
    print('gateway_id in update service_exposal: ', gateway_id)
    print('service to expose: ', service)
    service_info = prepare_gateway_node_service_entry(service)
    print('service_info :', service_info)
    mongo_add_gateway_service_to_node(gateway_id, service_info)
    print('after adding it to table: ', service_info)
    print('gateway_id new: ', gateway_id)
    mqtt_publish_new_firewall_rule(gateway_id, service_info)
    return


def handle_gateway_post(gateway_id, data):
    # TODO handle_gateway_post
    return

def handle_gateway_put(gateway_id, data):
    # TODO handle_gateway_put
    return

def handle_gateway_delete(gateway_id):
    # TODO handle_gateway_delete
    return

def prepare_gateway_node_service_entry(service):
    service['_id'] = ObjectId(service['_id'])
    return service


def register_netmanager(netmanager_data):
    net_id = mongo_register_netmanager_client(netmanager_data)
    if net_id is not None:
        return {'id': net_id}, 200
    return "", 500



def prepare_gateway_node_entry(worker_info, type):
    """
    @returns:
    {
        'gateway_id': string,
        'host': string,
        'host_port': int,
        'gateway_ipv4': string,
        'gateway_ipv6': string,
        'type': string,  <firewall,gateway>
        'used_ports': [],
        'services': []
    }
    """
    data = {}
    if type == 'firewall':
        # TODO adjust to more detailed worker info, from fetch whole node information
        data['gateway_id'] = worker_info['worker_id']
        data['gateway_ipv4'] = worker_info['publicip']
    
    if type == 'gateway':
        data['gateway_id'] = str(worker_info['_id'])
        if worker_info.get('ip') != "":
            data['gateway_ipv4'] = worker_info['ip']
        if worker_info.get('ipv6') != "":
            data['gateway_ipv6'] = worker_info['ipv6']
    data['host'] = worker_info['host']
    # TODO rename to host_port
    data['port'] = worker_info['port']
    data['type'] = type # type is either firewall or gateway
    data['used_ports'] = []
    data['services'] = []
    return data

def _is_public_IP(ip):
    """
    @return: boolean, whether address is from inside Oakestra network
    """
    addr = ipaddress.ip_address(ip)
    
    if addr == ipaddress.IPv4Address:
        oak_ipv4_net = ipaddress.ip_network("10.18.0.0/12")
        return addr not in oak_ipv4_net
    if addr == ipaddress.IPv6Address:
        oak_ipv6_net = ipaddress.ip_network("fc00::/7")
        return addr not in oak_ipv6_net
    return True
    
