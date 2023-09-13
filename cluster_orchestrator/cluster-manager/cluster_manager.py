import os
from flask import Flask, request
from flask_socketio import SocketIO, emit
import json
import socketio
import socket
import sys
from apscheduler.schedulers.background import BackgroundScheduler
import time
from prometheus_client import start_http_server
import threading
from mongodb_client import mongo_init, mongo_upsert_node, mongo_find_job_by_system_id, \
    mongo_update_job_status, mongo_find_node_by_name, mongo_find_job_by_id, mongo_remove_job_instance, \
    mongo_create_new_job_instance
from mqtt_client import mqtt_init, mqtt_publish_edge_deploy, mqtt_publish_edge_delete
from cluster_scheduler_requests import scheduler_request_deploy, scheduler_request_replicate, scheduler_request_status
from cm_logging import configure_logging
from system_manager_requests import send_aggregated_info_to_sm, re_deploy_dead_services_routine
from analyzing_workers import looking_for_dead_workers
from my_prometheus_client import prometheus_init_gauge_metrics, prometheus_set_metrics
from network_plugin_requests import *
import service_operations
import gateway_operations

MY_PORT = os.environ.get('MY_PORT')

MY_CHOSEN_CLUSTER_NAME = os.environ.get('CLUSTER_NAME')
MY_CLUSTER_LOCATION = os.environ.get('CLUSTER_LOCATION')
NETWORK_COMPONENT_PORT = os.environ.get('CLUSTER_SERVICE_MANAGER_PORT')
MY_ASSIGNED_CLUSTER_ID = None

SYSTEM_MANAGER_ADDR = 'http://' + os.environ.get('SYSTEM_MANAGER_URL') + ':' + os.environ.get('SYSTEM_MANAGER_PORT')
SYSTEM_MANAGER_ADDR_v6 = 'http://' + os.environ.get('SYSTEM_MANAGER_URL_v6') + ':' + os.environ.get('SYSTEM_MANAGER_PORT')

my_logger = configure_logging()

app = Flask(__name__)

# socketioserver = SocketIO(app, async_mode='eventlet', logger=, engineio_logger=logging)
socketioserver = SocketIO(app, logger=True, engineio_logger=True)

mongo_init(app)

mqtt_init(app)

sio = socketio.Client()

BACKGROUND_JOB_INTERVAL = 5


# ................... REST API Endpoints ...............#
# ......................................................#


@app.route('/')
def hello_world():
    app.logger.info('Hello World Request')
    app.logger.info('Processing default request')
    return "Hello, World! This is Cluster Manager's REST API - dual-stack enabled!"


@app.route('/status')
def status():
    app.logger.info('Incoming Request /status')
    return "ok", 200


@app.route('/api/deploy/<system_job_id>/<instance_number>', methods=['GET', 'POST'])
def deploy_task(system_job_id, instance_number):
    app.logger.info('Incoming Request /api/deploy')
    job = request.json  # contains job_id and job_description

    try:
        service_operations.deploy_service(job, system_job_id, instance_number)
    except Exception as e:
        return "", 500

    return 200


@app.route('/api/gateway/deploy', methods=['POST'])
def deploy_gateway():
    app.logger.info('Incoming Request /api/gateway/deploy')
    json_data = request.json  
    return gateway_operations.deploy_gateway(json_data)


@app.route('/api/gateway/<gateway_id>', methods=['POST, PUT', 'DELETE'])
def handle_gateway(gateway_id):
    app.logger.info('Incoming {} Request /api/gateway/{}'.format(request.method, gateway_id))
    json_data = request.json
    if request.method == 'POST':
        return gateway_operations.handle_gateway_post(gateway_id, json_data)
    if request.method == 'PUT':
        return gateway_operations.handle_gateway_put(gateway_id, json_data)
    if request.method == 'DELETE':
        return gateway_operations.handle_gateway_delete(gateway_id)


@app.route('/api/netmanager/register', methods=['POST'])
def register_netmanager():
    app.logger.info('Incoming Request /api/netmanager/register')
    json_data = request.json
    return gateway_operations.register_netmanager(json_data)


@app.route('/api/netmanager/<netmanager_id>', methods=['DELETE'])
def delete_netmanager(netmanager_id):
    app.logger.info('Incoming {} Request /api/netmanager/{}'.format(request.method, netmanager_id))
    return gateway_operations.delete_netmanager(netmanager_id)


@app.route('/api/result/<system_job_id>/<instance_number>', methods=['POST'])
def get_scheduler_result_and_propagate_to_edge(system_job_id, instance_number):
    # print(request)
    app.logger.info('Incoming Request /api/result - received cluster_scheduler result')
    data = request.json  # get POST body
    app.logger.info(data)

    if data.get('found',False):
        resulting_node_id = data.get('node').get('_id')

        mongo_update_job_status(system_job_id, instance_number, 'NODE_SCHEDULED', data.get('node'))
        job = mongo_find_job_by_system_id(system_job_id)

        # Inform network plugin about the deployment
        network_notify_deployment(str(job['system_job_id']), job)

        # Publish job
        mqtt_publish_edge_deploy(resulting_node_id, job, instance_number)
    else:
        mongo_update_job_status(system_job_id, instance_number, 'NO_WORKER_CAPACITY', None)
    return "ok"


@app.route('/api/delete/<system_job_id>/<instance_number>')
def delete_service(system_job_id, instance_number):
    """
    find service in db and ask corresponding worker to delete task,
    instance_number -1 undeploy all known instances
    """
    app.logger.info('Incoming Request /api/delete/ - to delete task...')

    try:
        service_operations.delete_service(system_job_id, instance_number)
    except Exception as e:
        return "", 500

    return "ok", 200


# ................ Scheduler Test ......................#
# ......................................................#


@app.route('/api/test/scheduler', methods=['GET'])
def scheduler_test():
    app.logger.info('Incoming Request /api/jobs - to get all jobs')
    return scheduler_request_status()


# ..................... REST handshake .................#
# ......................................................#

@app.route('/api/node/register', methods=['POST'])
def http_node_registration():
    app.logger.info('Incoming Request /api/node/register - to get all jobs')
    data = request.json  # get POST body
    registration_token = data.get("token")
    # TODO: check and generate tokens
    client_id = mongo_upsert_node({"ip": request.remote_addr, "node_info": data})
    response = {
        "id": str(client_id),
        "MQTT_BROKER_PORT": os.environ.get('MQTT_BROKER_PORT')
    }
    return response, 200


# ...... Websocket INIT Handling with edge nodes .......#
# ......................................................#

@socketioserver.on('connect', namespace='/init')
def on_connect():
    app.logger.info('Websocket - Client connected: {}'.format(request.remote_addr))
    emit('sc1', {'hello-edge': 'please send your node info'}, namespace='/init')


@socketioserver.on('cs1', namespace='/init')
def handle_init_worker(message):
    app.logger.info('Websocket - Received Edge_to_Cluster_Manager_1: {}'.format(request.remote_addr))
    app.logger.info(message)

    client_id = mongo_upsert_node({"ip": request.remote_addr, "node_info": json.loads(message)})

    init_packet = {
        "id": str(client_id),
        "MQTT_BROKER_PORT": os.environ.get('MQTT_BROKER_PORT')
    }

    # create ID and send it along with MQTT_Broker info to the client. save id into database
    emit('sc2', json.dumps(init_packet), namespace='/init')

    # no report here because regularly reports are sent anyways over mqtt.
    # cloud_request_incr_node(MY_ASSIGNED_CLUSTER_ID)  # report to system-manager about new edge node


@socketioserver.on('disconnect', namespace='/init')
def test_disconnect():
    app.logger.info('Websocket - Client disconnected')


# ........... BEGIN register to System Manager .........#
# ......................................................#

@sio.on('sc1', namespace='/register')
def handle_init_greeting(jsonarg):
    app.logger.info('Websocket - received System_Manager_to_Cluster_Manager_1 : ' + str(jsonarg))
    data = {
        'manager_port': MY_PORT,
        'network_component_port': NETWORK_COMPONENT_PORT,
        'cluster_name': MY_CHOSEN_CLUSTER_NAME,
        'cluster_info': {},
        'cluster_location': MY_CLUSTER_LOCATION
    }
    time.sleep(1)  # Wait to Avoid Race Condition!

    sio.emit('cs1', data, namespace='/register')
    app.logger.info('Websocket - Cluster Info sent. (Cluster_Manager_to_System_Manager)')


@sio.on('sc2', namespace='/register')
def handle_init_final(jsonarg):
    app.logger.info('Websocket - received System_Manager_to_Cluster_Manager_2:' + str(jsonarg))
    data = json.loads(jsonarg)

    app.logger.info("My received ID is: {}\n\n\n".format(data['id']))

    global MY_ASSIGNED_CLUSTER_ID
    MY_ASSIGNED_CLUSTER_ID = data['id']

    sio.disconnect()
    if MY_ASSIGNED_CLUSTER_ID is not None:
        app.logger.info('Received ID. Go ahead with Background Jobs')
        prometheus_init_gauge_metrics(MY_ASSIGNED_CLUSTER_ID)
        background_job_send_aggregated_information_to_sm()
    else:
        app.logger.info('No ID received.')


@sio.event()
def connect():
    app.logger.info("Websocket - I'm connected to System_Manager!")


@sio.event()
def connect_error(m):
    app.logger.info("Websocket connection failed with System_Manager!")


@sio.event()
def error(sid, data):
    app.logger.info('>>>> Websocket error with System_Manager <<<<< ')


@sio.event()
def disconnect(m):
    app.logger.info("Websocket disconnected with SM!")


def init_cm_to_sm():
    app.logger.info('Connecting to System_Manager...')
    try:
        sio.connect(SYSTEM_MANAGER_ADDR_v6 + '/register', namespaces=['/register'])
    except Exception as e:
        app.logger.error('SocketIO - Connection Establishment with System Manager failed!')
    time.sleep(1)


# ......... FINISH - register at System Manager ........#
# ......................................................#


def background_job_send_aggregated_information_to_sm():
    app.logger.info("Set up Background Jobs...")
    scheduler = BackgroundScheduler()
    job_send_info = scheduler.add_job(
        send_aggregated_info_to_sm,
        'interval',
        seconds=BACKGROUND_JOB_INTERVAL,
        kwargs={'my_id': MY_ASSIGNED_CLUSTER_ID,
                'time_interval': 2 * BACKGROUND_JOB_INTERVAL})
    job_dead_nodes = scheduler.add_job(
        looking_for_dead_workers,
        'interval',
        seconds=BACKGROUND_JOB_INTERVAL,
        kwargs={'interval': 2 * BACKGROUND_JOB_INTERVAL})
    job_re_deploy_dead_jobs = scheduler.add_job(
        re_deploy_dead_services_routine,
        'interval',
        seconds=BACKGROUND_JOB_INTERVAL)

    scheduler.start()


if __name__ == '__main__':
    # socketioserver.run(app, debug=True, host='0.0.0.0', port=MY_PORT)
    # app.run(debug=True, host='0.0.0.0', port=MY_PORT)

    start_http_server(10001)  # start prometheus server

    import eventlet

    init_cm_to_sm()
    eventlet.wsgi.server(eventlet.listen(('::', int(MY_PORT)), family=socket.AF_INET6), app, log=my_logger)  # see README for logging notes
