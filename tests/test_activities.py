from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


ACTIVITY_NAME = "Chess Club"
NEW_EMAIL = "newstudent@mergington.edu"


@pytest.fixture
def client():
    original_activities = deepcopy(activities)

    with TestClient(app) as test_client:
        yield test_client

    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_activity_details(client):
    # Arrange
    expected_fields = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert ACTIVITY_NAME in response.json()
    assert expected_fields <= response.json()[ACTIVITY_NAME].keys()


def test_signup_adds_participant(client):
    # Arrange
    email = NEW_EMAIL

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {ACTIVITY_NAME}"}
    assert email in activities[ACTIVITY_NAME]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": NEW_EMAIL}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_for_empty_email(client):
    # Arrange
    email = ""

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Email is required"


def test_signup_returns_400_for_duplicate_participant(client):
    # Arrange
    email = activities[ACTIVITY_NAME]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_returns_400_when_activity_is_full(client):
    # Arrange
    activity = activities[ACTIVITY_NAME]
    activity["max_participants"] = len(activity["participants"])

    # Act
    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": NEW_EMAIL}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_signup_returns_422_when_email_is_missing(client):
    # Arrange
    url = f"/activities/{ACTIVITY_NAME}/signup"

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 422


def test_unregister_removes_participant(client):
    # Arrange
    email = activities[ACTIVITY_NAME]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {ACTIVITY_NAME}"}
    assert email not in activities[ACTIVITY_NAME]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": NEW_EMAIL}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_unregistered_participant(client):
    # Arrange
    email = NEW_EMAIL

    # Act
    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"