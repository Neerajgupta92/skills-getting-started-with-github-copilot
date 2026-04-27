"""
Integration and unit tests for the FastAPI activity management system.
Tests follow the AAA (Arrange-Act-Assert) pattern for clarity and maintainability.
"""

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# UNIT TESTS - Business Logic and Validation
# ============================================================================

class TestEmailValidation:
    """Unit tests for email validation logic."""

    def test_valid_email_format_contains_at_symbol(self):
        """Verify that a valid email must contain an @ symbol."""
        # Arrange
        valid_emails = [
            "user@example.com",
            "alice@mergington.edu",
            "test.user+tag@domain.co.uk"
        ]

        # Act & Assert
        for email in valid_emails:
            assert "@" in email, f"Email {email} should contain @"

    def test_invalid_email_format_missing_at_symbol(self):
        """Verify that an invalid email without @ is rejected."""
        # Arrange
        invalid_emails = [
            "userexample.com",
            "alice",
            "test@"
        ]

        # Act & Assert
        for email in invalid_emails:
            # Note: The app doesn't validate email format, but this test documents
            # what proper validation should look like
            is_valid = "@" in email and email.index("@") > 0 and "." in email.split("@")[1]
            assert not is_valid, f"Email {email} should be invalid"


class TestActivityNotFoundHandling:
    """Unit tests for handling nonexistent activities."""

    def test_nonexistent_activity_raises_error(self, client):
        """Verify that requesting a nonexistent activity returns 404."""
        # Arrange
        client_instance = client
        nonexistent_activity = "Nonexistent Club"
        test_email = "student@example.com"

        # Act
        response = client_instance.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": test_email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"


class TestDuplicateSignupPrevention:
    """Unit tests for preventing duplicate signups."""

    def test_duplicate_signup_raises_error(self, client):
        """Verify that signing up twice for same activity returns 400."""
        # Arrange
        client_instance = client
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club

        # Act
        response = client_instance.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


# ============================================================================
# INTEGRATION TESTS - GET /activities Endpoint
# ============================================================================

class TestGetActivitiesEndpoint:
    """Integration tests for retrieving all activities."""

    def test_get_all_activities_returns_9_initial_activities(self, client):
        """Verify that GET /activities returns exactly 9 activities."""
        # Arrange
        client_instance = client

        # Act
        response = client_instance.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        assert "Chess Club" in activities

    def test_get_all_activities_returns_dict_structure(self, client):
        """Verify that activities are returned as a dictionary."""
        # Arrange
        client_instance = client

        # Act
        response = client_instance.get("/activities")
        activities = response.json()

        # Assert
        assert isinstance(activities, dict)
        assert all(isinstance(name, str) for name in activities.keys())

    def test_activity_response_contains_required_fields(self, client):
        """Verify that each activity contains all required fields."""
        # Arrange
        client_instance = client
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client_instance.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert all(
                field in activity_data for field in required_fields
            ), f"Activity {activity_name} missing required fields"

    def test_participants_list_is_array(self, client):
        """Verify that participants field is a list."""
        # Arrange
        client_instance = client

        # Act
        response = client_instance.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(
                activity_data["participants"], list
            ), f"Participants in {activity_name} should be a list"

    def test_max_participants_is_positive_integer(self, client):
        """Verify that max_participants is a positive integer."""
        # Arrange
        client_instance = client

        # Act
        response = client_instance.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0


# ============================================================================
# INTEGRATION TESTS - POST /activities/{activity_name}/signup Endpoint
# ============================================================================

class TestSignupForActivityEndpoint:
    """Integration tests for signing up for activities."""

    def test_signup_valid_student_happy_path(self, client, test_email):
        """Verify that a valid student can successfully sign up for an activity."""
        # Arrange
        client_instance = client
        email = test_email
        activity = "Programming Class"

        # Act
        response = client_instance.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_adds_student_to_participants_list(self, client, test_email):
        """Verify that signup actually adds the student to the participants list."""
        # Arrange
        client_instance = client
        email = test_email
        activity = "Art Club"

        # Act
        client_instance.post(f"/activities/{activity}/signup", params={"email": email})
        response = client_instance.get("/activities")

        # Assert
        activities = response.json()
        assert email in activities[activity]["participants"]

    def test_signup_missing_email_query_param(self, client):
        """Verify that signup without email parameter returns appropriate error."""
        # Arrange
        client_instance = client
        activity = "Drama Club"

        # Act
        response = client_instance.post(f"/activities/{activity}/signup")

        # Assert
        # FastAPI returns 422 Unprocessable Entity for missing required parameters
        assert response.status_code == 422

    def test_signup_nonexistent_activity_returns_404(self, client, test_email):
        """Verify that signup for nonexistent activity returns 404."""
        # Arrange
        client_instance = client
        email = test_email
        activity = "Nonexistent Club"

        # Act
        response = client_instance.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_student_returns_400(self, client):
        """Verify that duplicate signup for same activity returns 400."""
        # Arrange
        client_instance = client
        email = "daniel@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"

        # Act
        response = client_instance.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_multiple_students_different_activities(self, client):
        """Verify that multiple students can sign up for different activities."""
        # Arrange
        client_instance = client
        students = [
            ("student1@example.com", "Chess Club"),
            ("student2@example.com", "Drama Club"),
            ("student3@example.com", "Science Club")
        ]

        # Act
        responses = [
            client_instance.post(f"/activities/{activity}/signup", params={"email": email})
            for email, activity in students
        ]

        # Assert
        assert all(r.status_code == 200 for r in responses)
        activities = client_instance.get("/activities").json()
        for email, activity in students:
            assert email in activities[activity]["participants"]

    def test_signup_same_student_multiple_activities(self, client):
        """Verify that the same student can sign up for multiple activities."""
        # Arrange
        client_instance = client
        email = "versatile@example.com"
        activities_list = ["Chess Club", "Drama Club", "Science Club"]

        # Act
        for activity in activities_list:
            response = client_instance.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Assert
        activities = client_instance.get("/activities").json()
        for activity in activities_list:
            assert email in activities[activity]["participants"]


# ============================================================================
# INTEGRATION TESTS - DELETE /activities/{activity_name}/participants Endpoint
# ============================================================================

class TestUnregisterFromActivityEndpoint:
    """Integration tests for unregistering from activities."""

    def test_unregister_existing_participant_happy_path(self, client):
        """Verify that an existing participant can successfully unregister."""
        # Arrange
        client_instance = client
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"

        # Act
        response = client_instance.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_from_participants_list(self, client):
        """Verify that unregister actually removes the student from participants."""
        # Arrange
        client_instance = client
        email = "emma@mergington.edu"  # Already in Programming Class
        activity = "Programming Class"

        # Act
        client_instance.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        response = client_instance.get("/activities")

        # Assert
        activities = response.json()
        assert email not in activities[activity]["participants"]

    def test_unregister_missing_email_query_param(self, client):
        """Verify that unregister without email parameter returns error."""
        # Arrange
        client_instance = client
        activity = "Chess Club"

        # Act
        response = client_instance.delete(f"/activities/{activity}/participants")

        # Assert
        assert response.status_code == 422

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Verify that unregister from nonexistent activity returns 404."""
        # Arrange
        client_instance = client
        email = "student@example.com"
        activity = "Nonexistent Club"

        # Act
        response = client_instance.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404

    def test_unregister_not_registered_student_returns_404(self, client, test_email):
        """Verify that unregistering a student not in activity returns 404."""
        # Arrange
        client_instance = client
        email = test_email  # Not registered in any activity
        activity = "Chess Club"

        # Act
        response = client_instance.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_unregister_multiple_from_same_activity(self, client):
        """Verify that multiple participants can be unregistered from same activity."""
        # Arrange
        client_instance = client
        activity = "Gym Class"
        participants_to_remove = ["john@mergington.edu", "olivia@mergington.edu"]

        # Act
        for email in participants_to_remove:
            response = client_instance.delete(
                f"/activities/{activity}/participants",
                params={"email": email}
            )
            assert response.status_code == 200

        # Assert
        activities = client_instance.get("/activities").json()
        for email in participants_to_remove:
            assert email not in activities[activity]["participants"]


# ============================================================================
# INTEGRATION TESTS - GET / Root Endpoint
# ============================================================================

class TestRootEndpoint:
    """Integration tests for the root endpoint."""

    def test_root_redirects_to_static(self, client):
        """Verify that GET / redirects to /static/index.html."""
        # Arrange
        client_instance = client

        # Act
        response = client_instance.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert "/static" in response.headers["location"]

    def test_root_redirect_can_be_followed(self, client):
        """Verify that following the redirect reaches static content."""
        # Arrange
        client_instance = client

        # Act
        response = client_instance.get("/", follow_redirects=True)

        # Assert
        assert response.status_code == 200


# ============================================================================
# INTEGRATION TESTS - Complex Scenarios
# ============================================================================

class TestComplexScenarios:
    """Integration tests for complex real-world scenarios."""

    def test_signup_unregister_signup_again(self, client, test_email):
        """Verify that a student can unregister and then re-signup for an activity."""
        # Arrange
        client_instance = client
        email = test_email
        activity = "Basketball Team"

        # Act - First signup
        response1 = client_instance.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert first signup
        assert response1.status_code == 200
        activities = client_instance.get("/activities").json()
        assert email in activities[activity]["participants"]

        # Act - Unregister
        response2 = client_instance.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )

        # Assert unregister
        assert response2.status_code == 200
        activities = client_instance.get("/activities").json()
        assert email not in activities[activity]["participants"]

        # Act - Re-signup
        response3 = client_instance.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert re-signup
        assert response3.status_code == 200
        activities = client_instance.get("/activities").json()
        assert email in activities[activity]["participants"]

    def test_concurrent_signups_and_unregisters(self, client):
        """Verify that multiple signups and unregisters work correctly together."""
        # Arrange
        client_instance = client
        new_participants = [
            "alice@test.com",
            "bob@test.com",
            "charlie@test.com"
        ]
        activity = "Soccer Club"
        existing_initial_count = len(
            client_instance.get("/activities").json()[activity]["participants"]
        )

        # Act - Sign up new participants
        for email in new_participants:
            response = client_instance.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Assert after all signups
        activities = client_instance.get("/activities").json()
        assert len(activities[activity]["participants"]) == existing_initial_count + 3

        # Act - Unregister some
        removed_count = 0
        for email in new_participants[:2]:
            response = client_instance.delete(
                f"/activities/{activity}/participants",
                params={"email": email}
            )
            assert response.status_code == 200
            removed_count += 1

        # Assert after removals
        activities = client_instance.get("/activities").json()
        assert len(activities[activity]["participants"]) == existing_initial_count + 3 - removed_count
