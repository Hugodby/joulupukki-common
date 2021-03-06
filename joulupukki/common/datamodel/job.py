import time
import json
import os

import pecan
import wsme
import wsme.types as wtypes

from joulupukki.common.database import mongo
from joulupukki.common.datamodel import types
#from joulupukki.common.datamodel.user import User
#from joulupukki.common.datamodel.project import Project
#from joulupukki.common.datamodel.build import Build
from joulupukki.common.distros import supported_distros, reverse_supported_distros

source_types = wtypes.Enum(str, 'local', 'git')


class APIJob(types.Base):
    pass


class Job(APIJob):
    id_ = wsme.wsattr(int, mandatory=False)
    created = wsme.wsattr(float, mandatory=False)
    distro = wsme.wsattr(wtypes.text, mandatory=False)
    status = wsme.wsattr(wtypes.text, mandatory=False)
#    build_time = wsme.wsattr(float, mandatory=False)
    finished = wsme.wsattr(float, mandatory=False, default=None)
    # TODO guess which user is...
    # Links
    username = wsme.wsattr(wtypes.text, mandatory=False)
    project_name = wsme.wsattr(wtypes.text, mandatory=False)
    build_id = wsme.wsattr(int, mandatory=False)

    def __init__(self, data=None):
        if data is None:
            APIJob.__init__(self)
        if isinstance(data, APIJob):
            APIJob.__init__(self, **data.as_dict())
        else:
            APIJob.__init__(self, **data)
        self.user = None
        self.project = None
        self.build = None

    @classmethod
    def sample(cls):
        # TODO
        return cls(
            source_url="https://github.com/kaji-project/shinken.git",
            source_type="git",
            branch="master",
        )

    def create(self):
        # Check required args
        required_args = ['distro',
                         'username',
                         'project_name',
                         'build_id']
        for arg in required_args:
            if not getattr(self, arg):
                # TODO handle error
                return False
        # Get last ids
        self.id_ = 1
        jobs_ids = [
            x.get("id_")
            for x in mongo.jobs.find(
                {"username": self.username, "project_name": self.project_name,
                 "build_id": self.build_id},
                ["id_"]
            )
        ]
        if jobs_ids:
            self.id_ = max(jobs_ids) + 1
        # Set attributes
        self.created = time.time()
        self.status = "created"

        # TODO: check password
        # Write project data
        try:
            self._save()
            return True
        except Exception as exp:
            # TODO handle error
            return False



    def _save(self):
        """ Write job data on disk """
        data = self.as_dict()
        mongo.jobs.update({"id_": self.id_,
                           "username": self.username,
                           "project_name": self.project_name,
                           "build_id": self.build_id},
                           data,
                           upsert=True)
        return True




    def get_folder_output(self):
        """ Return build folder path"""
        if self.distro != "osx":
            self.distro = reverse_supported_distros.get(self.distro, self.distro)
        else:
            self.distro = "osx"
        return os.path.join(pecan.conf.workspace_path,
                            self.username,
                            self.project_name,
                            "builds",
                            str(self.build_id),
                            "output",
                            self.distro,
                            )

    def get_folder_path(self):
        """ Return build folder path"""
        return os.path.join(pecan.conf.workspace_path,
                            self.username,
                            self.project_name,
                            "builds",
                            str(self.build_id),
                            "jobs",
                            str(self.id_),
                            )

    def get_folder_tmp(self):
        return os.path.join(self.get_folder_path(), "tmp")


    def set_status(self, status):
        self.status = status
        self._save()


    def set_build_time(self, build_time):
        self.build_time = build_time
        self._save()


    def set_end_time(self, end_time):
        self.finished = end_time
        self._save()


    @classmethod
    def fetch(cls, build, id_):
        job_data = mongo.jobs.find_one({"username": build.username,
                                        "project_name": build.project_name,
                                        "build_id": build.id_,
                                        "id_": int(id_)})
        if job_data is not None:
            return cls(job_data)
        return None

    @classmethod
    def fetch_from_dict(job_dict):
        job_data = mongo.jobs.find_one({"username": job_dict['username'],
                                        "project_name": job_dict['project_name'],
                                        "build_id": job_dict['id_'],
                                        "id_": int(id_)})
        if job_data is not None:
            return cls(job_data)
        return None



    def dumps(self):
        dump = self.as_dict()
        return dump



    def get_log(self):
        log_file = os.path.join(self.get_folder_path(), "log.txt")
        log = ""
        # Read status_file
        with open(log_file, 'r') as f:
            try:
                log = f.read()
            except Exception as exp:
                return
        return log
