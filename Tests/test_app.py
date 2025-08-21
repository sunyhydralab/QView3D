import os
import re
import pytest
from Classes.Loggers.Logger import Logger
from parallel_test_runner import testLevel

def __desc__(): return "App Tests"

@pytest.mark.dependency()
@pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
def test_db_to_make_sure_it_has_valid_file_path(app):
    db_file_no_path = app.config["SQLALCHEMY_DATABASE_URI"].split("/")[-1].split("\\")[-1]
    assert db_file_no_path, "database_uri doesn't exist?"
    assert db_file_no_path == "QView.db", f"database_uri is {db_file_no_path}"
    assert os.path.exists(app.config["SQLALCHEMY_DATABASE_URI"].split("sqlite:///")[
                              -1]), f"Database file {app.config["SQLALCHEMY_DATABASE_URI"].split("sqlite:///")[-1]} does not exist"


@pytest.mark.dependency(depends=["test_db_to_make_sure_it_has_valid_file_path"])
@pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
def test_base_url_for_http_responses_has_valid_format(app):
    assert app.config["base_url"], "base_url doesnt exist?"
    assert re.match(r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$", app.config["base_url"]) or re.match(
        r"http://localhost:\d{1,5}$", app.config["base_url"]), f"base_url is {app.config['base_url']}"


@pytest.mark.dependency(depends=["test_base_url_for_http_responses_has_valid_format"])
@pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
def test_environment_for_development(app):
    assert app.config["environment"], "environment doesnt exist?"
    assert app.config["environment"] == "development", f"environment is {app.config['environment']}"


@pytest.mark.dependency(depends=["test_environment_for_development"])
@pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
def test_logger_is_custom_implementation_and_exists(app):
    assert app.logger, "myLogger doesnt exist?"
    assert app.logger.name, "name doesnt exist?"
    assert str(app.logger.name) == "Logger_App", f"myLogger is {str(app.logger.name)}"
    assert isinstance(app.logger, Logger), "myLogger is not an instance of Logger?"
    assert app.logger.fileLogger, "fileLogger doesnt exist?"


@pytest.mark.dependency(depends=["test_logger_is_custom_implementation_and_exists"])
@pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
def test_socketio_exists_and_works(app):
    assert app.socketio, "socketio doesnt exist?"
    assert app.socketio.async_mode, "async_mode doesnt exist?"
    assert app.socketio.async_mode == "threading", f"async_mode is {app.socketio.async_mode}"
    socketio_test_client = app.socketio.test_client(app)
    assert socketio_test_client.is_connected(), "socketio_test_client is not connected?"
    socketio_test_client.emit('my_event', {'data': 'test'})
    received = socketio_test_client.get_received()
    assert len(received) == 0, "Response received from socketio"


@pytest.mark.dependency(depends=["test_socketio_exists_and_works"])
@pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
def test_handle_errors_and_logging(app):
    assert app.handle_errors_and_logging, "handle_errors_and_logging doesnt exist?"
    assert callable(app.handle_errors_and_logging), "handle_errors_and_logging is not callable?"
    assert app.handle_errors_and_logging(Exception("Test Exception")) is False, "handle_errors_and_logging did not return False?"


@pytest.mark.dependency(depends=["test_handle_errors_and_logging"])
@pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
def test_static_loading_for_client(app):
    assert app.static_folder, "static_folder doesnt exist?"
    assert os.path.join("client","dist") in app.static_folder, f"static_folder is {app.static_folder}"
    assert os.path.exists(app.static_folder), f"static_folder {app.static_folder} does not exist"


@pytest.mark.dependency(depends=["test_static_loading_for_client"])
@pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
def test_index_html_exists_in_the_static_files(app):
    assert os.path.exists(os.path.join(app.static_folder, "index.html")), f"index.html does not exist in {app.static_folder}"


@pytest.mark.dependency(depends=["test_index_html_exists_in_the_static_files"])
@pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
def test_main_view_response_is_200(app):
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200, f"Response status code is {response.status_code}"
        assert response.data, "Response data is empty?"
        assert b'<!DOCTYPE html>' in response.data, "Response data does not contain <!DOCTYPE html>?"
        assert b'<html' in response.data, "Response data does not contain <html>?"
        assert b'<head>' in response.data, "Response data does not contain <head>?"
        assert b'<title>' in response.data, "Response data does not contain <title>?"
        assert b'<body>' in response.data, "Response data does not contain <body>?"
        assert b'<div id="app">' in response.data, 'Response data does not contain <div id="app">?'
        assert b'<script type="module" crossorigin src=' in response.data, 'Response data does not contain <script type="module" crossorigin src=?'
        assert b'<link rel="stylesheet" crossorigin href=' in response.data, 'Response data does not contain <link rel="stylesheet" crossorigin href=?'
        assert b'</body>' in response.data, "Response data does not contain </body>?"
        assert b'</html>' in response.data, "Response data does not contain </html>?"

# @pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
# def test_queue_view_response(app):
#     with app.test_client() as client:
#         response = client.get('/queue')
#         assert response.status_code == 200, f"Response status code is {response.status_code}"
#         assert response.data, "Response data is empty?"
#         assert b'<!DOCTYPE html>' in response.data, "Response data does not contain <!DOCTYPE html>?"
#         assert b'<html' in response.data, "Response data does not contain <html>?"
#         assert b'<head>' in response.data, "Response data does not contain <head>?"
#         assert b'<title>' in response.data, "Response data does not contain <title>?"
#         assert b'<body>' in response.data, "Response data does not contain <body>?"
#         assert b'<div id="app">' in response.data, 'Response data does not contain <div id="app">?'
#         assert b'<script type="module" crossorigin src=' in response.data, 'Response data does not contain <script type="module" crossorigin src=?'
#         assert b'<link rel="stylesheet" crossorigin href=' in response.data, 'Response data does not contain <link rel="stylesheet" crossorigin href=?'
#         assert b'</body>' in response.data, "Response data does not contain </body>?"
#         assert b'</html>' in response.data, "Response data does not contain </html>?"
#
# @pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
# def test_registered_view_response(app):
#     with app.test_client() as client:
#         response = client.get('/registration')
#         assert response.status_code == 200, f"Response status code is {response.status_code}"
#         assert response.data, "Response data is empty?"
#         assert b'<!DOCTYPE html>' in response.data, "Response data does not contain <!DOCTYPE html>?"
#         assert b'<html' in response.data, "Response data does not contain <html>?"
#         assert b'<head>' in response.data, "Response data does not contain <head>?"
#         assert b'<title>' in response.data, "Response data does not contain <title>?"
#         assert b'<body>' in response.data, "Response data does not contain <body>?"
#         assert b'<div id="app">' in response.data, 'Response data does not contain <div id="app">?'
#         assert b'<script type="module" crossorigin src=' in response.data, 'Response data does not contain <script type="module" crossorigin src=?'
#         assert b'<link rel="stylesheet" crossorigin href=' in response.data, 'Response data does not contain <link rel="stylesheet" crossorigin href=?'
#         assert b'</body>' in response.data, "Response data does not contain </body>?"
#         assert b'</html>' in response.data, "Response data does not contain </html>?"
#
# @pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
# def test_error_view_response(app):
#     with app.test_client() as client:
#         response = client.get('/error')
#         assert response.status_code == 200, f"Response status code is {response.status_code}"
#         assert response.data, "Response data is empty?"
#         assert b'<!DOCTYPE html>' in response.data, "Response data does not contain <!DOCTYPE html>?"
#         assert b'<html' in response.data, "Response data does not contain <html>?"
#         assert b'<head>' in response.data, "Response data does not contain <head>?"
#         assert b'<title>' in response.data, "Response data does not contain <title>?"
#         assert b'<body>' in response.data, "Response data does not contain <body>?"
#         assert b'<div id="app">' in response.data, 'Response data does not contain <div id="app">?'
#         assert b'<script type="module" crossorigin src=' in response.data, 'Response data does not contain <script type="module" crossorigin src=?'
#         assert b'<link rel="stylesheet" crossorigin href=' in response.data, 'Response data does not contain <link rel="stylesheet" crossorigin href=?'
#         assert b'</body>' in response.data, "Response data does not contain </body>?"
#         assert b'</html>' in response.data, "Response data does not contain </html>?"