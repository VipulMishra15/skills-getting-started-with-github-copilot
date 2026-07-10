"""
Smoke tests for Mergington High School FastAPI application

Tests cover the main API endpoints using the AAA (Arrange-Act-Assert) pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Fixture that provides a TestClient and resets activities state before each test.
    
    Creates fresh test activities and yields a TestClient instance.
    The fixture resets the activities dictionary before each test to ensure
    test isolation.
    """
    # Arrange: Reset activities to a known test state
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["alice@mergington.edu", "bob@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["charlie@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in theatrical productions",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": []
        }
    })
    
    # Return fresh TestClient for this test
    yield TestClient(app)


def test_get_activities_returns_all_activities(client):
    """
    Test that GET /activities returns all activities successfully.
    
    Verifies the endpoint returns a 200 status code and all activities
    are present in the response.
    """
    # Arrange
    expected_activities = ["Chess Club", "Programming Class", "Drama Club"]
    
    # Act
    response = client.get("/activities")
    
    # Assert
    assert response.status_code == 200
    returned_activities = response.json()
    assert len(returned_activities) == 3
    for activity_name in expected_activities:
        assert activity_name in returned_activities


def test_signup_new_participant_success(client):
    """
    Test successful signup for a new participant to an activity.
    
    Verifies that a new participant can successfully sign up for an activity
    and receives a 200 status code with confirmation message.
    """
    # Arrange
    activity_name = "Chess Club"
    new_email = "diane@mergington.edu"
    original_participant_count = len(activities[activity_name]["participants"])
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
    assert new_email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == original_participant_count + 1


def test_signup_activity_not_found_returns_404(client):
    """
    Test that signup returns 404 when activity does not exist.
    
    Verifies that attempting to sign up for a non-existent activity
    returns a 404 error with appropriate error message.
    """
    # Arrange
    nonexistent_activity = "Nonexistent Club"
    email = "diane@mergington.edu"
    
    # Act
    response = client.post(
        f"/activities/{nonexistent_activity}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_participant_returns_400(client):
    """
    Test that signup returns 400 when participant already signed up.
    
    Verifies that attempting to sign up again with an email already
    registered returns a 400 error with appropriate error message.
    """
    # Arrange
    activity_name = "Chess Club"
    existing_email = "alice@mergington.edu"
    original_participant_count = len(activities[activity_name]["participants"])
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email}
    )
    
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert len(activities[activity_name]["participants"]) == original_participant_count


def test_unregister_participant_success(client):
    """
    Test successful unregistration of a participant from an activity.
    
    Verifies that a registered participant can successfully unregister
    from an activity and receives a 200 status code with confirmation.
    """
    # Arrange
    activity_name = "Chess Club"
    email_to_remove = "alice@mergington.edu"
    original_participant_count = len(activities[activity_name]["participants"])
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email_to_remove}
    )
    
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email_to_remove} from {activity_name}"
    assert email_to_remove not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == original_participant_count - 1


def test_unregister_activity_not_found_returns_404(client):
    """
    Test that unregister returns 404 when activity does not exist.
    
    Verifies that attempting to unregister from a non-existent activity
    returns a 404 error with appropriate error message.
    """
    # Arrange
    nonexistent_activity = "Nonexistent Club"
    email = "alice@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{nonexistent_activity}/unregister",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_registered_participant_returns_400(client):
    """
    Test that unregister returns 400 when participant is not registered.
    
    Verifies that attempting to unregister a participant who is not
    registered returns a 400 error with appropriate error message.
    """
    # Arrange
    activity_name = "Drama Club"  # Empty participants list
    email = "not_registered@mergington.edu"
    original_participant_count = len(activities[activity_name]["participants"])
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student not signed up for this activity"
    assert len(activities[activity_name]["participants"]) == original_participant_count


def test_signup_unregister_signup_integration(client):
    """
    Integration test: signup, unregister, then signup again.
    
    Verifies that a participant can sign up for an activity, unregister,
    and then successfully sign up again, demonstrating full state transitions.
    """
    # Arrange
    activity_name = "Drama Club"
    email = "frank@mergington.edu"
    
    # Act - Sign up
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert - Successfully signed up
    assert signup_response.status_code == 200
    assert email in activities[activity_name]["participants"]
    
    # Act - Unregister
    unregister_response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )
    
    # Assert - Successfully unregistered
    assert unregister_response.status_code == 200
    assert email not in activities[activity_name]["participants"]
    
    # Act - Sign up again
    signup_again_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert - Successfully signed up again
    assert signup_again_response.status_code == 200
    assert email in activities[activity_name]["participants"]
