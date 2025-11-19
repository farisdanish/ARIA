"""API routes."""
from flask_restx import Api
from flask import Blueprint

apiroute = Blueprint('apiroute', __name__, url_prefix='/api')
api = Api(apiroute, doc='/docs/', title='ARIA API', version='1.0')

from . import routes

ns = routes.ns
# Add namespace to API (API is already bound to blueprint, no need for init_app)
api.add_namespace(ns)

__all__ = ['apiroute', 'api', 'ns']

