import logging

from re import search
from ext_requests.gateway_db import *
from ext_requests.cluster_requests import cluster_request_to_deploy_gateway, cluster_request_to_update_gateway
from ext_requests.net_plugin_requests import net_inform_firewall_deploy
from sla.versioned_sla_parser import parse_sla_json


def create_service_gateway(current_user, sla):
    data = parse_sla_json(sla)
    logging.log(logging.INFO, sla)
    services = data.get('microservices')

    for microservice in services:

        # check if microserviceID is set
        if microservice.get("microserviceID") is None:
            return {'message': "microserviceID cannot be empty"}, 404

        # check if service is deployed
        service = mongo_get_service_instances_by_id(microservice["microserviceID"])
        if service is None:
            return {'message': "service {} not found".format(microservice["microserviceID"])}, 404
        
        # check if service is already exposed
        duplicate = mongo_get_gateway_service_by_id(microservice["microserviceID"])
        if duplicate is not None:
            return {'message': "service {} already exposed".format(microservice["microserviceID"])}, 404
        
        # fetch the internal port correctly
        # here we try to extract the non-docker-internal port on the target machine
        try: 
            port = search(':(.+)', service['port']).group(1)
        except AttributeError:
            port = service['port']
        # remove protocol at the end, if present
        microservice["internal_port"] = int(port.split('/')[0]) # internal port

        # add the service to be exposed to collection of exposed services
        mongo_add_service_to_gatewaydb(microservice)
        microservice['_id'] = str(microservice['_id'])

        # fetch the clusters of running target service instances
        clusters = mongo_get_clusters_of_active_service_instances(microservice['microserviceID'])
        for cluster in clusters:
            # notify clusters to enable gateway for microservice if possible
            cluster_request_to_deploy_gateway(cluster, microservice)

    return {'message': 'service(s) successfully exposed'}, 200


def get_service_gateway(user, service_id):
    return

def delete_service_gateway(user, service_id):
    return

