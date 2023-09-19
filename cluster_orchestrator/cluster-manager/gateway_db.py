import mongodb_client as db
from bson import ObjectId

def mongo_add_gateway_service(service):
    db.app.logger.info("MONGODB - insert service to gateway db...")
    new_service = db.mongo_gateway_services.insert_one(service)
    inserted_id = new_service.inserted_id
    db.app.logger.info("MONGODB - service {} added to gateway db".format(str(inserted_id))) 
    return str(inserted_id)


def mongo_add_gateway_service_to_node(node_id, service):
    db.mongo_gateway_nodes.update_one({'worker_id': node_id},
                                   {'$addToSet': {'services': service}})


def mongo_add_gateway_node(gateway):
    db.app.logger.info("MONGODB - insert node to gateway db...")
    new_gateway = db.mongo_gateway_nodes.insert_one(gateway)
    inserted_id = new_gateway.inserted_id
    db.app.logger.info("MONGODB - service {} added to gateway db".format(str(inserted_id))) 
    return str(inserted_id)


def mongo_get_gateway_service(service_id):
    return db.mongo_gateway_services.find_one({'microserviceID': service_id})

def mongo_get_gateway_node(node_id):
    return db.mongo_gateway_nodes.find_one({'worker_id': node_id})

def mongo_delete_gateway_service(service_id):
    return

def mongo_delete_gateway_node(gateway_id):
    return


def mongo_get_gateways_of_cluster():
    return db.mongo_gateway_nodes.find({'type': 'gateway'})


def mongo_get_service_by_exposed_port(port_num):
    return db.mongo_gateway_services.find_one({'exposed_port': port_num})


def mongo_check_if_port_already_used(port_num):
    return db.mongo_gateway_services.find_one({'exposed_port': port_num}).limit(1).size()


def mongo_get_service_instance_node_information(service_id):
    return db.mongo_jobs.db.jobs.find_one({'microserviceID': service_id}, {'instance_list.worker_id': 1, 'instance_list.publicip': 1})


def mongo_register_netmanager_client(netmanager_data):
    db.app.logger.info("MONGODB - insert netmanager to gateway netmanager db...")
    new_gateway = db.mongo_gateway_netmanagers.insert_one(netmanager_data)
    inserted_id = new_gateway.inserted_id
    db.app.logger.info("MONGODB - service {} added to gateway netmanagers db".format(str(inserted_id))) 
    return str(inserted_id)

def mongo_delete_netmanager_client(netmanager_id):
    db.app.logger.info("MONGODB - delete netmanager from gateway netmanager db...")
    db.mongo_gateway_netmanagers.delete(ObjectId(netmanager_id))
    db.app.logger.info("MONGODB - deleted netmanager client {} from gateway netmanagers db".format(netmanager_id)) 

def mongo_find_available_idle_worker():
    # TODO tidy entry return
    return db.mongo_gateway_netmanagers.find_one()

def mongo_find_available_gateway_by_port(port):
    return db.mongo_gateway_nodes.find_one({'used_ports': {'$nin': [port]}})

def mongo_get_gateways_of_service(service_id):
    return db.mongo_gateway_nodes.find({'microservices': service_id})