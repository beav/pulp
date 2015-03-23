import logging

from mongoengine import Document, StringField, DateTimeField

from pulp.common.constants import SCHEDULER_WORKER_NAME
from pulp.server.async.celery_instance import RESOURCE_MANAGER_QUEUE
from pulp.server.db.model.base import CriteriaQuerySet
from pulp.server.db.model.resources import ReservedResource
from pulp.server.exceptions import NoWorkers


_logger = logging.getLogger(__name__)


class Worker(Document):
    """
    Represents a worker.

    This inherits from mongoengine.Document and defines the schema for the documents
    in the worker collection.

    :ivar worker_name:    worker name, in the form of "worker_type@hostname"
    :type worker_name:    basestring
    :ivar last_heartbeat:  ISO8601 representation of the time the task started executing
    :type last_heartbeat:  basestring
    """
    name = StringField(primary_key=True)
    last_heartbeat = DateTimeField()

    meta = {'collection': 'workers',
            'indexes': [],  # this is a small collection that does not need an index
            'allow_inheritance': False,
            'queryset_class': CriteriaQuerySet}

    @property
    def queue_name(self):
        """
        This property is a convenience for getting the queue_name that Celery assigns to this
        Worker.

        :return: The name of the queue that this Worker is uniquely subcribed to.
        :rtype:  basestring
        """
        return "%(name)s.dq" % {'name': self.name}

    @classmethod
    def _is_worker(cls, worker_name):
        """
        Strip out workers that should never be assigned work. We need to check
        via "startswith()" since we do not know which host the worker is running on.
        """

        if worker_name.startswith(SCHEDULER_WORKER_NAME) or \
           worker_name.startswith(RESOURCE_MANAGER_QUEUE):
            return False
        return True

    @classmethod
    def get_unreserved_worker(cls):
        """
        Return the Worker instance that has no reserved_resource entries
        associated with it. If there are no unreserved workers a
        pulp.server.exceptions.NoWorkers exception is raised.

        :raises NoWorkers: If all workers have reserved_resource entries associated with them.

        :returns:          The Worker instance that has no reserved_resource
                           entries associated with it.
        :rtype:            pulp.server.db.model.resources.Worker
        """

        # Build a mapping of queue names to Worker objects
        workers_dict = dict((worker['name'], worker) for worker in cls.objects())
        worker_names = [name for name in workers_dict.keys()]
        reserved_names = [r['worker_name'] for r in ReservedResource.get_collection().find()]

        # Find an unreserved worker using set differences of the names, and filter
        # out workers that should not be assigned work.
        # NB: this is a little messy but set comprehensions are in python 2.7+
        unreserved_workers = set(filter(cls._is_worker, worker_names)) - set(reserved_names)

        try:
            return workers_dict[unreserved_workers.pop()]
        except KeyError:
            # All workers are reserved
            raise NoWorkers()

    @classmethod
    def get_worker_for_reservation(cls, resource_id):
        """
        Return the Worker instance that is associated with a reservation of type resource_id. If
        there are no workers with that reservation_id type a pulp.server.exceptions.NoWorkers
        exception is raised.

        :param resource_id:    The name of the resource you wish to reserve for your task.

        :raises NoWorkers:     If all workers have reserved_resource entries associated with them.

        :type resource_id:     basestring
        :returns:              The Worker instance that has a reserved_resource entry of type
                               `resource_id` associated with it.
        :rtype:                pulp.server.db.model.resources.Worker
        """
        reservation = ReservedResource.get_collection().find_one({'resource_id': resource_id})
        if reservation:
            return cls.objects(name=reservation['worker_name']).first()
        else:
            raise NoWorkers()
