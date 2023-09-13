import json
import traceback

from bson import json_util
from flask import request, Response, jsonify
from flask.views import MethodView
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, Api, abort

from blueprints.schema_wrapper import SchemaWrapper
from services.gateway_management import *
from roles.securityUtils import *

from sla.schema import gateway_schema

# ........ Functions for gateway management ...............#
# .........................................................#

gatewayblp = Blueprint(
    'Gateway operations', 'gateway', url_prefix='/api/gateway',
    description='Operations on gateway network functions'
)

gateway_registration_schema = service_response_schema = {
    "type": "object",
    "properties": {
        "gateway_name": {"type": "string"},
        "gateway_ip": {
            "type": "array",
            "items": {"type": "string"}
            },
        "microservice_id": {"type": "string"},
        "exposed": {"type": "integer"},
    }
}

gateway_response_schema = {
    "type": "array",
    "items": {
        "gateway_id": {"type": "string"},
        "gateway_ipv4": {"type": "string"},
        "gateway_ipv6": {"type": "string"},
        "services": {
            "type": "array",
            "items": {
                "service_id": {"type": "string"},
                "internal_port": {"type": "integer"},
                "exposed_port": {"type": "integer"}
            }
        }
    }
}

@gatewayblp.route('/')
class GatewayController(Resource):
    @gatewayblp.arguments(schema=gateway_schema, location="json", validate=False, unknown=True)
    @gatewayblp.response(200, SchemaWrapper(gateway_registration_schema), content_type="application/json")
    @jwt_required()
    def post(self, *args, **kwargs):
        data = request.get_json()
        current_user = get_jwt_identity()
        result, code = create_service_gateway(current_user, data)
        if code != 200:
            abort(code, result)
        return json_util.dumps(result)


@gatewayblp.route('/<service_id>')
class GatewayServiceController(Resource):

    @gatewayblp.response(200, SchemaWrapper(service_response_schema), content_type="application/json")
    @jwt_auth_required()
    def get(self, serviceid):
        """Get gateways for specific service ID

        Requires user to own the service
        ---
        """
        username = get_jwt_auth_identity()
        job = get_service_gateway(serviceid, username)
        if job is not None:
            return json_util.dumps(job)
        else:
            return abort(404, "not found")

    @gatewayblp.response(200, content_type="application/json")
    @jwt_required()
    def delete(self, service_id):
        """Remove gateways for specific service ID
        Causes all gateways to close the exposed service port
        
        Requires user to own the service
        ---
        """
        try:
            username = get_jwt_auth_identity()
            if delete_service_gateway(username, service_id):
                return {"message": "Service exposure removed"}
            else:
                abort(500, "Could not delete service exposure")
        except ConnectionError as e:
            abort(500, e)
        

# For the Admin to get all gateways
@gatewayblp.route('/')
class MultipleGatewayController(Resource):

    @gatewayblp.response(200, SchemaWrapper(gateway_response_schema), content_type="application/json")
    @jwt_required()
    @require_role(Role.ADMIN)
    def get(self, *args, **kwargs):
        return json_util.dumps(mongo_get_all_gateways())
