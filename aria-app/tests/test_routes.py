def test_home_page_access(client):
    """Test that the home page loading correctly when not logged in."""
    response = client.get('/')
    assert response.status_code == 200

def test_api_routes_available(client):
    """Test that the api route namespace is accessible and returns 404 (or 200 doc string) but not a 500 error."""
    response = client.get('/api/docs/')
    assert response.status_code in [200, 404]

def test_student_login_protection(client):
    """Test that /homeStud route is protected by login_required."""
    response = client.get('/homeStud')
    # Should redirect to login (302) or return unauthorized (401)
    assert response.status_code in [302, 401]
