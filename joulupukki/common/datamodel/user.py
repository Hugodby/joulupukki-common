import os
import shutil

import pecan
import wsme
import json
import wsme.types as wtypes

from joulupukki.common.database import mongo
from joulupukki.common.utils import encrypt_password, check_password, create_token
from joulupukki.common.datamodel import types
#from joulupukki.web.controllers.v2.datamodel.project import Project
from joulupukki.common.datamodel.project import Project


class APIUser(types.Base):
    username = wsme.wsattr(wtypes.text, mandatory=True)
    password = wsme.wsattr(wtypes.text, mandatory=False)
    email = wsme.wsattr(wtypes.text, mandatory=False)
    name = wsme.wsattr(wtypes.text, mandatory=False)

class User(APIUser):
    projects = wsme.wsattr([Project], mandatory=False)
    orgs = wsme.wsattr([wtypes.text], mandatory=False)
    token = wsme.wsattr(wtypes.text, mandatory=False)
    token_github = wsme.wsattr(wtypes.text, mandatory=False)
    token_gitlab = wsme.wsattr(wtypes.text, mandatory=False)
    id_gitlab = wsme.wsattr(int, mandatory=False)
    gitlab_group = wsme.wsattr(bool, mandatory=False, default=False)

    def __init__(self, data=None, sub_objects=True):
        if data is None:
            APIUser.__init__(self)
        if isinstance(data, APIUser):
            APIUser.__init__(self, **data.as_dict())
        else:
            APIUser.__init__(self, **data)
        if sub_objects:
            self.projects = self.get_projects()

    @classmethod
    def sample(cls):
        return cls(
            username="joulupukkit",
            email="admin@joulupukkit.local",
            password="packer",
        )

    @classmethod
    def fetch(cls, username, with_password=True, sub_objects=True):
        db_user = mongo.users.find_one({"username": username})
        user = None
        if db_user is not None:
           user = cls(db_user, sub_objects=sub_objects)
           if not with_password:
                delattr(user, 'password')
        return user

    def create(self):
        # Check required args
        required_args = ['username',
                         'email',
#                         'password',
                        ]
        for arg in required_args:
            if not hasattr(self, arg):
                # TODO handle error
                return False
        # Create token
        self.token = create_token() 
        # Encrypt password
        if self.password:
            self.password = encrypt_password(self.password)
        # Write user data
        try:
            self._save()
            return True
        except Exception as exp:
            # TODO handle error
            return False

    def update(self, new_user_data, access_token=None):
        # Remove no editable args
        calculed_args = ['token',
                         'username',
                         'Id',
                        ]
        for arg in calculed_args:
            if hasattr(new_user_data, arg):
                delattr(new_user_data, arg)
        # Check password
        if pecan.conf.auth is None:
            if not check_password(new_user_data.password, self.password):
                # TODO bas password
                return False
        elif pecan.conf.auth == 'github':
            if self.token_github != access_token:
                return False
        # Set new values
        for key, val in new_user_data.as_dict().items():
            # We don't want to modify password
            if key == 'password':
                continue
            setattr(self, key, val)
        # Write user data
        try:
            self._save()
            return self
        except Exception as exp:
            # TODO handle 
            return False


    def _save(self):
        """ Write user data on disk """
        data = self.as_dict()
        # TODO Delete useless data
        if 'projects' in data:
            data['projects'] = []
        mongo.users.update({"username": self.username}, data, upsert=True)
        return True


    def delete(self, password):
        # Check password
        if not check_password(password, self.password):
            # TODO bas password
            return False
        try:
            mongo.users.remove({"username": self.username})
            return True
        except Exception as exp:
            # TODO handle 
            return False

    def get_projects(self):
        projects = mongo.projects.find({"username": self.username})
        return [Project(x) for x in projects]

           
    @classmethod
    def fetch_from_github_token(cls, token_github, sub_objects=True):
        db_user = mongo.users.find_one({"token_github": token_github})
        user = None
        if db_user is not None:
           user = cls(db_user, sub_objects=sub_objects)
           delattr(user, 'password')
        return user

    @classmethod
    def fetch_from_gitlab_token(cls, token_gitlab, sub_objects=True):
        db_user = mongo.users.find_one({"token_gitlab": token_gitlab})
        user = None
        if db_user is not None:
           user = cls(db_user, sub_objects=sub_objects)
           delattr(user, 'password')
        return user
