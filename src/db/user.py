# -*- coding: UTF-8 -*-

"""User mongodb adapter

Users have a status (student or teacher) and location (room,
seat).


"""

from tornado.gen import coroutine
from src.utils import random_word
from .common import db, ConditionNotMetError
from .db_object import DBObject


class User(DBObject):
    coll = db.users
    defaults = {
        'status': 'none',
        'room_name': None,
        'room_code': 'none',
        'instances': 0,
    }

    @classmethod
    @coroutine
    def from_google_userinfo(cls, userinfo):
        """Create a User object from google's userinfo data.

        Sample userinfo data::

            {'family_name': 'Ganter',
             'given_name': 'Cristóbal',
             'kind': 'plus#personOpenIdConnect',
             'locale': 'es',
             'name': 'Cristóbal Ganter',
             'picture': 'https://lh4.googleusercontent.com/
                         -HDGdhHDjlh/AAAAAAAAAAI/
                         LJGDDJHK765K/-Nuvyyib864/photo.jpg?
                         sz=50',
             'profile': 'https://plus.google.com/
                         738259437132941462401',
             'sub': '738259437132941462401'}
        """
        yield cls.coll.update(
            {'_id': userinfo['sub']},
            {
                '$set': {'google_userinfo': userinfo}
            },
            upsert=True)
        self = yield cls(userinfo['sub'])
        return self

    def __str__(self):
        return self.name

    def __repr__(self):
        return "User('%s')" % self.id

    @property
    def secret(self):
        if 'secret' in self._data:
            return self._data['secret']
        else:
            secret = random_word(20)
            self.store('secret', secret)
            return secret

    @property
    def name(self):
        return self.google_userinfo['name']

    @coroutine
    def increase_instances(self):
        yield self.modify(
            {
                '$inc': {'instances': 1}
            }
        )

    @coroutine
    def decrease_instances(self):
        try:
            yield self.modify_if(
                {
                    'instances': {'$gt': 0}
                },
                {
                    '$inc': {'instances': -1}
                }
            )
            yield self.store_dict_if(
                {'instances': 0},
                {'status': self.defaults['status']}
            )
        except ConditionNotMetError:
            pass
