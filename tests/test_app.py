"""Tests for the High School Management System API"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to known state before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name in activities:
        activities[name]["participants"] = original_activities[name]["participants"].copy()


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns 200 OK"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_has_expected_keys(self, client):
        """Test that activities have expected structure"""
        response = client.get("/activities")
        activities_data = response.json()
        
        assert "Chess Club" in activities_data
        assert "Programming Class" in activities_data
        assert "Gym Class" in activities_data
        assert "Debate Club" in activities_data
        assert "Art Studio" in activities_data
        assert "Science Club" in activities_data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_data in activities_data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_returns_200(self, client, reset_activities):
        """Test that signup returns 200 OK"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup adds participant to activity"""
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()["Chess Club"]["participants"]
        initial_count = len(initial_participants)
        
        client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        final_response = client.get("/activities")
        final_participants = final_response.json()["Chess Club"]["participants"]
        
        assert len(final_participants) == initial_count + 1
        assert "newstudent@mergington.edu" in final_participants

    def test_signup_returns_success_message(self, client, reset_activities):
        """Test that signup returns correct success message"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert "test@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signup to nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_multiple_students(self, client, reset_activities):
        """Test that multiple students can sign up"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            client.post(
                f"/activities/Programming%20Class/signup?email={email}"
            )
        
        response = client.get("/activities")
        participants = response.json()["Programming Class"]["participants"]
        
        for email in emails:
            assert email in participants


class TestUnregisterFromActivity:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_returns_200(self, client, reset_activities):
        """Test that unregister returns 200 OK"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes participant from activity"""
        initial_response = client.get("/activities")
        initial_participants = initial_response.json()["Chess Club"]["participants"]
        initial_count = len(initial_participants)
        
        client.post(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        
        final_response = client.get("/activities")
        final_participants = final_response.json()["Chess Club"]["participants"]
        
        assert len(final_participants) == initial_count - 1
        assert "michael@mergington.edu" not in final_participants

    def test_unregister_returns_success_message(self, client, reset_activities):
        """Test that unregister returns correct success message"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test that unregister from nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_nonexistent_participant_returns_400(self, client, reset_activities):
        """Test that unregister of nonexistent participant returns 400"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_signup_then_unregister(self, client, reset_activities):
        """Test complete signup and unregister workflow"""
        email = "workflow@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            f"/activities/Debate%20Club/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        check_response = client.get("/activities")
        assert email in check_response.json()["Debate Club"]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/Debate%20Club/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister
        final_response = client.get("/activities")
        assert email not in final_response.json()["Debate Club"]["participants"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects(self, client):
        """Test that root endpoint redirects"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
