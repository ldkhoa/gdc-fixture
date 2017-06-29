import json
import logging
import os
import re
import requests
import requests.auth
import pystache
import time
import uuid


def die(error):
    logging.error(error)
    raise error if isinstance(error, BaseException) else RuntimeError(error)


class TimeoutException(Exception):
    pass


class Fixture(object):
    required_files = ['model.maql', 'upload_info.json', 'upload.zip']

    def __init__(self, path):
        self.path = path
        missed = set(self.required_files) - set(os.listdir(path))
        if len(missed) > 0:
            die(OSError('Required file(s) missed in %s: %s' % (
                         path,
                         ', '.join(missed)
            )))

    def __str__(self):
        return self.path

    def __getitem__(self, item):
        return os.path.join(self.path, item)

    def get_file(self, filename, mode='r'):
        return open(self[filename], mode=mode)

    def read_file(self, filename):
        with self.get_file(filename) as f:
            return f.read()


class Project(object):
    def __init__(self, gd_session, project):
        self.gd = gd_session
        self.project = project
        self.id_to_uri = {}

    def get_link(self):
        return self.project['project']['links']['self']

    def get_md_link(self):
        return self.project['project']['links']['metadata']

    def get_manage_link(self):
        return self.get_md_link() + '/ldm/manage2'

    def get_etl_link(self):
        return self.get_md_link() + '/etl/pull2'

    def get_identifiers_link(self):
        return self.get_md_link() + '/identifiers'

    def get_obj_link(self):
        return self.get_md_link() + '/obj?createAndGet=true'

    @staticmethod
    def parse_ids_from_maql(maql):
        return list(set(
            [match.group(1) for match in re.finditer('{([\w\.]*)}', maql)]
        ))

    @staticmethod
    def get_md_object_uri(object_hash):
        return next(object_hash.itervalues())['meta']['uri']

    def identifiers_to_uris(self, identifiers):
        identifiers_payload = {
            'identifierToUri': identifiers
        }
        objs = self.gd.post(
            self.get_identifiers_link(),
            data=identifiers_payload
        ).json()['identifiers']
        id_uris = [
            (obj['identifier'].replace('.', '_'), obj['uri']) for obj in objs
        ]
        self.id_to_uri.update(id_uris)

    def ldm2_manage(self, maql):
        manage_uri = self.get_manage_link()
        manage_data = {'manage': {'maql': maql}}
        logging.info('Updating model %s' % manage_uri)
        post_maql = self.gd.post(manage_uri, data=manage_data)
        manage_status_uri = post_maql.json()['entries'][0]['link']
        return self.gd.get_while(
            manage_status_uri,
            path=['wTaskStatus', 'status'],
            value='RUNNING'
        )

    def upload_data(self, upload_file):
        uploads_dir = str(uuid.uuid4())
        uploads_uri = '/uploads/' + uploads_dir
        upload_zip_uri = '%s/upload.zip' % uploads_uri

        logging.info('Uploading to WebDAV %s' % upload_zip_uri)
        self.gd.mkcol(uploads_uri)
        self.gd.webdav_upload(upload_zip_uri, upload_file)

        etl_data = {'pullIntegration': uploads_dir}
        etl_uri = self.get_etl_link()

        logging.info('Loading from WebDAV to project %s' % etl_uri)
        post_etl = self.gd.post(etl_uri, data=etl_data)
        etl_status_uri = post_etl.json()['pull2Task']['links']['poll']
        return self.gd.get_until(
            etl_status_uri,
            path=['wTaskStatus', 'status'],
            expected_value='OK',
            error_value='ERROR'
        )

    def create_md_object(self, name, content):
        logging.debug('Creating MD object %s' % name)
        post_content = pystache.render(
            json.dumps(content),
            context=self.id_to_uri
        )
        obj = self.gd.post(self.get_obj_link(), data=post_content)
        if obj.status_code != 200:
            die('Error while creating object %s - response %s:\n%s' % (
                 name,
                 obj.status_code,
                 obj.text
            ))

        self.id_to_uri[name] = self.get_md_object_uri(obj.json())

    def apply_fixture(self, fixture):
        maql = fixture.read_file('model.maql')
        ids = self.parse_ids_from_maql(maql)
        md_fixture = json.loads(fixture.read_file('metadata.json'))
        if 'import_identifiers' in md_fixture:
            ids += md_fixture['import_identifiers']
        self.ldm2_manage(maql)
        self.identifiers_to_uris(ids)
        with fixture.get_file('upload.zip', mode='rb') as zip_file:
            self.upload_data(zip_file)
        for obj in md_fixture['objects']:
            self.create_md_object(obj['name'], obj['content'])


class GoodData(object):
    def __init__(self, baseurl, login, password):
        self.baseurl = baseurl
        self.login = login
        self.password = password
        self.session = requests.Session()
        self.session.auth = self.get_auth()
        self.webdav_session = None
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        login_payload = {
            'postUserLogin': {
                'login': login,
                'password': password,
                'remember': 1,
            }
        }
        login = self.post('/gdc/account/login', data=login_payload)
        if login.status_code != 200:
            die('Failed to login to %s: %s' % (baseurl, login.text))
        user_login = login.json()['userLogin']
        self.user_profile = user_login['profile']
        self.user_state = user_login['state']
        logging.debug('Logged in as %s' % self.user_profile)

    @staticmethod
    def nested_dict_value(_dict, path):
        val = _dict
        for x in path:
            val = val[x]
        return val

    def get(self, uri):
        return self.session.get(self.baseurl + uri, headers=self.headers)

    def post(self, uri, data, expected_status=None):
        if expected_status is None:
            expected_status = [200, 201]
        post_data = data if type(data) in [unicode, str] else json.dumps(data)
        try:
            response = self.session.post(
                self.baseurl + uri,
                data=post_data,
                headers=self.headers
            )
            logging.debug(
                'POST %s X-GDC-REQUEST: %s' % (
                    uri,
                    response.headers.get('X-GDC-REQUEST', 'none')
                )
            )
            if response.status_code not in expected_status:
                die('Unexpected POST %s status %s:\n%s' % (
                    uri,
                    response.status_code,
                    response.text
                ))
            return response
        except Exception as e:
            die(e)

    def get_auth(self):
        return requests.auth.HTTPBasicAuth(self.login, self.password)

    def get_webdav_session(self):
        if self.webdav_session is None:
            self.webdav_session = requests.session()
        return self.webdav_session

    def mkcol(self, uri):
        return self.get_webdav_session().request(
            'MKCOL',
            url=self.baseurl + uri,
            auth=self.get_auth()
        )

    def webdav_upload(self, uri, upload_file):
        upload_url = self.baseurl + uri
        self.get_webdav_session().put(
            upload_url,
            data=upload_file,
            auth=self.get_auth()
        )

    def get_until(
            self,
            uri,
            path,
            expected_value,
            error_value=None,
            timeout_secs=60,
            poll_secs=0.5):
        wait_time = timeout_secs
        while wait_time >= 0:
            response = self.get(uri)
            check_value = self.nested_dict_value(response.json(), path)
            if check_value == expected_value:
                return response
            elif error_value is not None and check_value == error_value:
                die('Got error value %s=%s while polling %s\n%s' % (
                    '.'.join(path),
                    check_value,
                    uri,
                    response.text
                ))
            wait_time -= poll_secs
            time.sleep(poll_secs)
        die(TimeoutException('poll timeout %s' % uri))

    def get_while(self, uri, path, value, timeout_secs=60, poll_secs=0.5):
        wait_time = timeout_secs
        while wait_time >= 0:
            response = self.get(uri)
            check_value = self.nested_dict_value(response.json(), path)
            if value != check_value:
                return response
            wait_time -= poll_secs
            time.sleep(poll_secs)
        die(TimeoutException('poll timeout %s' % uri))

    def create_project(
            self,
            title,
            summary,
            driver='Pg',
            pgroup='pgroup2',
            environment='TESTING'):
        project_data = {
            'project': {
                'content': {
                    'authorizationToken': pgroup,
                    'driver': driver,
                    'environment': environment,
                    'guidedNavigation': 1,
                },
                'meta': {
                    'summary': summary,
                    'title': title,
                }
            }
        }
        project_uri = self.post(
            '/gdc/projects/',
            data=project_data
        ).json()['uri']
        final_response = self.get_until(
            project_uri,
            path=['project', 'content', 'state'],
            expected_value='ENABLED',
            error_value='DELETED'
        )
        logging.info('Created project %s' % project_uri)
        return Project(self, final_response.json())

    def open_project(self, project_id):
        return Project(
            self,
            self.get('/gdc/projects/' + project_id).json()
        )

    def update_project(self, fixture, project_id):
        self.open_project(project_id).apply_fixture(fixture)

    def deploy_fixture(
            self,
            fixture,
            project_title,
            project_summary='',
            driver='Pg',
            pgroup='pgroup2',
            environment='TESTING'):
        project = self.create_project(
            project_title,
            project_summary,
            driver,
            pgroup,
            environment)
        project.apply_fixture(fixture)
