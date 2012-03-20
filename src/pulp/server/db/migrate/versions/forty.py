# -*- coding: utf-8 -*-

# Copyright © 2010-2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import logging

from pulp.server.db.model.resource import Repo

_log = logging.getLogger('pulp')

version = 40


def _migrate_repos():
    repo_coln = Repo.get_collection()
    repo_coln.update({}, {"$set": {"sync_options.skip": {"distribution": 1}}},
        multi=True)

def migrate():
    _log.info('migration to data model version %d started' % version)
    _migrate_repos()
    _log.info('migration to data model version %d complete' % version)
