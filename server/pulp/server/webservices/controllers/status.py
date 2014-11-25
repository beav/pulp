# -*- coding: utf-8 -*-
#
# Copyright © 2013 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the License
# (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied, including the
# implied warranties of MERCHANTABILITY, NON-INFRINGEMENT, or FITNESS FOR A
# PARTICULAR PURPOSE.
# You should have received a copy of GPLv2 along with this software; if not,
# see http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt

"""
Unauthenticated status API so that other can make sure we're up (to no good).
"""

import web

import pulp.server.managers.factory as managers

from pulp.server.webservices.controllers.base import JSONController

# status controller ------------------------------------------------------------

class StatusController(JSONController):

    def GET(self):
        status_manager = managers.status_manager()
        topic_manager = managers.topic_publish_manager()

        pulp_version = status_manager.get_version()
        pulp_workers = [w for w in status_manager.get_workers()]
        pulp_messaging_connection = status_manager.get_broker_conn_status()

        status_data = {'api_version': '2',
                       'pulp_version': pulp_version,
                       'pulp_messaging_connection': pulp_messaging_connection,
                       'workers': pulp_workers}

        return self.ok(status_data)

# web.py application -----------------------------------------------------------

URLS = ('/', StatusController)

application = web.application(URLS, globals())
