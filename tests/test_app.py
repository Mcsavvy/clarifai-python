import logging
import os
from datetime import datetime

import pytest

from clarifai.client.app import App
from clarifai.client.user import User
from clarifai.constants.search import DEFAULT_TOP_K

NOW = str(int(datetime.now().timestamp()))
MAIN_APP_ID = "main"
MAIN_APP_USER_ID = "clarifai"
GENERAL_MODEL_ID = "general-image-recognition"
General_Workflow_ID = "General"

CREATE_APP_USER_ID = os.environ["CLARIFAI_USER_ID"]
CREATE_APP_ID = f"ci_test_app_{NOW}"
CREATE_MODEL_ID = f"ci_test_model_{NOW}"
CREATE_DATASET_ID = f"ci_test_dataset_{NOW}"
CREATE_MODULE_ID = f"ci_test_module_{NOW}"
CREATE_RUNNER_ID = f"ci_test_runner_{NOW}"

CLARIFAI_PAT = os.environ["CLARIFAI_PAT"]


@pytest.fixture
def create_app():
  return App(user_id=CREATE_APP_USER_ID, app_id=CREATE_APP_ID, pat=CLARIFAI_PAT)


@pytest.fixture
def app():
  return App(user_id=MAIN_APP_USER_ID, app_id=MAIN_APP_ID, pat=CLARIFAI_PAT)


@pytest.fixture
def client():
  return User(user_id=MAIN_APP_USER_ID, pat=CLARIFAI_PAT)


@pytest.mark.requires_secrets
class TestApp:
  """Tests for the App class and its methods.

    CRUD operations are tested for each of the following resources:
    - app
    - dataset
    - model
    - workflow

    Note: Update to be added later.
    """

  def test_list_models(self, app):
    all_models = list(app.list_models(page_no=2))
    assert len(all_models) == 16  #default per_page is 16

  def test_list_workflows(self, app):
    all_workflows = list(app.list_workflows(page_no=1, per_page=10))
    assert len(all_workflows) == 10

  def test_list_apps(self, client):
    all_apps = list(client.list_apps())
    assert len(all_apps) > 0

  def test_get_model(self, client):
    model = client.app(app_id=MAIN_APP_ID).model(model_id=GENERAL_MODEL_ID)
    assert model.id == GENERAL_MODEL_ID and model.app_id == MAIN_APP_ID and model.user_id == MAIN_APP_USER_ID

  def test_get_workflow(self, client):
    workflow = client.app(app_id=MAIN_APP_ID).workflow(workflow_id=General_Workflow_ID)
    assert workflow.id == General_Workflow_ID and workflow.app_id == MAIN_APP_ID and workflow.user_id == MAIN_APP_USER_ID

  def test_create_app(self):
    app = User(user_id=CREATE_APP_USER_ID, pat=CLARIFAI_PAT).create_app(app_id=CREATE_APP_ID)
    assert app.id == CREATE_APP_ID and app.user_id == CREATE_APP_USER_ID

  def test_create_search(self, create_app):
    search = create_app.search()
    assert search.top_k == DEFAULT_TOP_K and search.metric_distance == "COSINE_DISTANCE"

  def test_create_dataset(self, create_app):
    dataset = create_app.create_dataset(CREATE_DATASET_ID)
    assert dataset.id == CREATE_DATASET_ID and dataset.app_id == CREATE_APP_ID and dataset.user_id == CREATE_APP_USER_ID

  def test_create_model(self, create_app):
    model = create_app.create_model(CREATE_MODEL_ID)
    assert model.id == CREATE_MODEL_ID and model.app_id == CREATE_APP_ID and model.user_id == CREATE_APP_USER_ID

  def test_create_module(self, create_app):
    module = create_app.create_module(CREATE_MODULE_ID, description="CI test module")
    assert module.id == CREATE_MODULE_ID and module.app_id == CREATE_APP_ID and module.user_id == CREATE_APP_USER_ID

  def test_create_runner(self, client):
    client = User(user_id=CREATE_APP_USER_ID, pat=CLARIFAI_PAT)
    runner = client.create_runner(
        CREATE_RUNNER_ID, labels=["ci runner"], description="CI test runner")
    assert runner.id == CREATE_RUNNER_ID and runner.user_id == CREATE_APP_USER_ID

  def test_get_dataset(self, create_app):
    dataset = create_app.dataset(dataset_id=CREATE_DATASET_ID)
    assert dataset.id == CREATE_DATASET_ID and dataset.app_id == CREATE_APP_ID and dataset.user_id == CREATE_APP_USER_ID

  def test_list_datasets(self, create_app):
    all_datasets = list(create_app.list_datasets())
    assert len(all_datasets) == 1

  def test_delete_dataset(self, create_app, caplog):
    with caplog.at_level(logging.INFO):
      create_app.delete_dataset(CREATE_DATASET_ID)
      assert "SUCCESS" in caplog.text

  def test_delete_model(self, create_app, caplog):
    with caplog.at_level(logging.INFO):
      create_app.delete_model(CREATE_MODEL_ID)
      assert "SUCCESS" in caplog.text

  def test_delete_module(self, create_app, caplog):
    with caplog.at_level(logging.INFO):
      create_app.delete_module(CREATE_MODULE_ID)
      assert "SUCCESS" in caplog.text

  def test_delete_runner(self, caplog):
    client = User(user_id=CREATE_APP_USER_ID)
    with caplog.at_level(logging.INFO):
      client.delete_runner(CREATE_RUNNER_ID)
      assert "SUCCESS" in caplog.text

  def test_delete_app(self, caplog):
    with caplog.at_level(logging.INFO):
      User(user_id=CREATE_APP_USER_ID).delete_app(CREATE_APP_ID)
      assert "SUCCESS" in caplog.text
