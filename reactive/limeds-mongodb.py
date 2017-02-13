#!/usr/bin/env python3
# Copyright (C) 2017  Ghent University
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import requests
import jinja2

from charmhelpers.core.hookenv import status_set, config, charm_dir


from charms.reactive import when, when_not


@when_not('limeds.available')
def no_limeds_connected():
    status_set(
        'waiting',
        'Waiting for LimeDS to become available.')


@when('limeds.available', 'mongodb.available')
def limeds_connected(limeds_relation, mongodb_relation):
    conf = config()
    installable_id = conf.get('installable-id')
    installable_version = conf.get('installable-version')
    instance_id = conf.get('instance-id')
    database = conf.get('database')
    connection_string = mongodb_relation.connection_string()
    count = 0

    with open("{}/templates/mongodb-config.json".format(charm_dir()), 'r') as conf_file:
        mongo_conf = jinja2.Template(conf_file.read())

    for unit in limeds_relation.units:
        count += 1
        deploy_url = "{limeds_url}/_limeds/installables"\
                     "/{installable_id}/{installable_version}"\
                     "/deploy".format(
                         limeds_url=unit['url'],
                         installable_id=installable_id,
                         installable_version=installable_version)
        print("configuring LimeDS, adding installable: {}".format(deploy_url))
        response = requests.get(deploy_url, headers={"Accept": "application/json"})
        if not response.status_code == 200:
            print("ERROR: Deploying installable failed: {} {}".format(
                response.status_code,
                response.text))

        factory_url = "{limeds_url}/_limeds/config"\
                      "/{installable_id}.Factory".format(
                          limeds_url=unit['url'],
                          installable_id=installable_id, )
        formatted_conf = mongo_conf.render(
            instance_id=instance_id,
            database=database,
            connection_string=connection_string, )
        print("Creating instance: {}, \n {}".format(factory_url, formatted_conf))
        response = requests.post(
            factory_url,
            headers={"Accept": "application/json"},
            data=formatted_conf, )
        if not response.status_code == 200:
            print("ERROR: Deploying installable failed: {} {}".format(
                response.status_code,
                response.text))
        status_set('active', 'Ready ({} units)'.format(count))
