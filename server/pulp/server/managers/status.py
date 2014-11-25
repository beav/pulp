"""
This module contains management functions for finding the Pulp version
"""

from pkg_resources import get_distribution
from pulp.server.managers import resources
from pulp.server.db.model.criteria import Criteria

from pulp.server.async.celery_instance import celery as app

class StatusManager(object):

    def get_version(self):
        """
        :returns:          Pulp platform version
        :rtype:            string
        """
        return get_distribution("pulp-server").version

    def get_workers(self):
        """
        :returns:          list of workers with their heartbeats
        """
        empty_criteria = Criteria()
        return resources.filter_workers(empty_criteria)

    def get_broker_conn_status(self):
        """
        :returns:          connection
        """
        # XXX: This does not return what you expect!
        conn = app.connection() 
        return conn.connected
