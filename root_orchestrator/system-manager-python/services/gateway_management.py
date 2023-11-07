import logging

from re import search
from ext_requests.gateway_db import *
from ext_requests.apps_db import mongo_find_job_by_id
from ext_requests.cluster_requests import cluster_request_to_deploy_gateway, cluster_request_to_update_gateway
from ext_requests.net_plugin_requests import net_inform_firewall_deploy
from sla.versioned_sla_parser import parse_sla_json


def create_service_gateway(current_user, sla):
    data = parse_sla_json(sla)
    logging.log(logging.INFO, sla)
    services = data.get('microservices')

    gateway_table = {}

    for microservice in services:

        # check if microserviceID is set
        if microservice.get("microserviceID") is None:
            return {'message': "microserviceID cannot be empty"}, 500

        # check if service is deployed
        service = mongo_get_service_instances_by_id(microservice["microserviceID"])
        if service is None:
            return {'message': "service {} not found".format(microservice["microserviceID"])}, 500
        
        # check if service is already exposed
        duplicate = mongo_get_gateway_service_by_id(microservice["microserviceID"])
        if duplicate is not None:
            return {'message': "service {} already exposed".format(microservice["microserviceID"])}, 500
        
        # fetch the internal port correctly
        # here we try to extract the non-docker-internal port on the target machine
        try: 
            port = search(':(.+)', service['port']).group(1)
        except AttributeError:
            port = service['port']
        # remove protocol at the end, if present
        microservice["internal_port"] = int(port.split('/')[0]) # internal port
        microservice["job_name"] = service["job_name"]

        # add the service to be exposed to collection of exposed services
        mongo_add_service_to_gatewaydb(microservice)
        microservice['_id'] = str(microservice['_id'])

        # fetch the clusters of running target service instances
        clusters = mongo_get_clusters_of_active_service_instances(microservice['microserviceID'])
        for cluster in clusters:
            # notify clusters to enable gateway for microservice if possible
            deployment_status = cluster_request_to_deploy_gateway(cluster, microservice)
            if deployment_status != 200:
                # TODO: add cleanup
                return {'message': 'cluster {} could not deploy gateway. Aborting.'.format(cluster)}, 500
    
    # fetch gateways of service and add to return table
    # FIXME: implement me 
    # gateway_table[microservice['microserviceID']] = gateways
    return {'message': 'service(s) successfully exposed'}, 200


def get_service_gateway(user, service_id):
    return {'message' 'implement me!'}, 200

def delete_service_gateway(user, service_id):
    return {'message' 'implement me!'}, 200

