import pytest
import falcon
import json
from jwt import jwk_from_dict
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from test_utils.token_stuff import keys_json, user_token,\
    admin_token, invalid_token


def get_keys():
    data = json.loads(keys_json)
    keys = []
    for k in data['keys']:
        jwk = jwk_from_dict(k)
        print(jwk.keyobj.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))
        keys.append(jwk)

    print("Number of imported keys :" + str(len(keys)))
    print("Keys: {}".format(keys))
    return keys


@pytest.mark.parametrize("body, expected_status",
                         [({'modelName': 'test', 'modelVersion': 3, 'endpointName': 'test',
                            'subjectName': 'test'}, falcon.HTTP_OK)])
def test_add_endpoint_auth_valid_user_token(mocker, client_with_auth, body, expected_status):
    create_endpoint_mock = mocker.patch('management_api.endpoints.endpoints.create_endpoint')
    create_endpoint_mock.return_value = "test"
    time_mock = mocker.patch('time.time')
    time_mock.return_value = 1538148672.765898  # Friday 28th September 2018
    get_keys_mock = mocker.patch('management_api.authenticate.auth_controller._get_keys_from_dex')
    get_keys_mock.side_effect = get_keys
    header = {'Authorization': user_token}
    result = client_with_auth.simulate_request(method='POST', path='/endpoints',
                                               headers=header, json=body)
    assert expected_status == result.status


@pytest.mark.parametrize("body, expected_status",
                         [({'modelName': 'test', 'modelVersion': 3, 'endpointName': 'test',
                            'subjectName': 'test'}, falcon.HTTP_401)])
def test_add_endpoint_auth_expired_token(mocker, client_with_auth, body, expected_status):
    create_endpoint_mock = mocker.patch('management_api.endpoints.endpoints.create_endpoint')
    create_endpoint_mock.return_value = "test"
    time_mock = mocker.patch('time.time')
    time_mock.return_value = 2538148672.765898  # far far away in the future
    get_keys_mock = mocker.patch('management_api.authenticate.auth_controller._get_keys_from_dex')
    get_keys_mock.side_effect = get_keys
    header = {'Authorization': user_token}
    result = client_with_auth.simulate_request(method='POST', path='/endpoints',
                                               headers=header, json=body)
    assert expected_status == result.status


@pytest.mark.parametrize("body, expected_status",
                         [("", falcon.HTTP_401)])
def test_call_endpoint_with_invalid_token(mocker, client_with_auth, body, expected_status):
    get_keys_mock = mocker.patch('management_api.authenticate.auth_controller._get_keys_from_dex')
    get_keys_mock.side_effect = get_keys
    header = {'Authorization': invalid_token}
    result = client_with_auth.simulate_request(method='POST', path='/endpoints',
                                               headers=header, json=body)
    assert expected_status == result.status


@pytest.mark.parametrize("body, expected_status",
                         [("", falcon.HTTP_403)])
def test_create_tenant_with_user_token(mocker, client_with_auth, body, expected_status):
    time_mock = mocker.patch('time.time')
    time_mock.return_value = 1538148672.765898  # Friday 28th September 2018
    get_keys_mock = mocker.patch('management_api.authenticate.auth_controller._get_keys_from_dex')
    get_keys_mock.side_effect = get_keys
    header = {'Authorization': user_token}
    result = client_with_auth.simulate_request(method='POST', path='/tenants',
                                               headers=header, json=body)
    assert expected_status == result.status


@pytest.mark.parametrize("body, expected_status",
                         [("Wrong payload", falcon.HTTP_400)])
def test_create_tenant_with_user_admin(mocker, client_with_auth, body, expected_status):
    # HTTP 400 means we passsed token verification
    time_mock = mocker.patch('time.time')
    time_mock.return_value = 1538148672.765898  # Friday 28th September 2018
    get_keys_mock = mocker.patch('management_api.authenticate.auth_controller._get_keys_from_dex')
    get_keys_mock.side_effect = get_keys
    header = {'Authorization': admin_token}
    result = client_with_auth.simulate_request(method='POST', path='/tenants',
                                               headers=header, json=body)
    assert expected_status == result.status
