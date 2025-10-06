import pytest


@pytest.mark.e2e
def test_org_lifecycle(gitea_client):
    """
    Full organization lifecycle:
    1. create organization
    2. list orgs for user
    3. fetch org details
    4. update organization description
    5. (optional) delete organization — skipped if unsupported
    """

    username = "org_owner"
    email = "org_owner@example.com"
    password = "Password123!"
    org_name = "sample-org"

    # Ensure user exists
    resp = gitea_client.create_user(username=username, email=email, password=password)
    assert resp.ok() or resp.status_code in (409, 422), \
        f"User creation failed: {resp.status_code} {getattr(resp, 'text', '')}"

    # 1. Create organization
    resp = gitea_client.admin_create_org(owner_username=username, org_name=org_name, description="Initial org")
    assert resp.ok() or resp.status_code in (409, 422), \
        f"Org creation failed: {resp.status_code} {getattr(resp, 'text', '')}"

    org_data = resp.json if resp.ok() else {}
    if org_data:
        assert org_data.get("username") == org_name or org_data.get("full_name") == org_name, \
            f"Unexpected org data: {org_data}"

    # 2. List orgs for user
    resp = gitea_client.list_orgs()
    assert resp.ok(), f"List orgs failed: {resp.status_code} {getattr(resp, 'text', '')}"
    orgs = [o.get("username") or o.get("full_name") for o in resp.json]
    assert org_name in orgs, f"Expected {org_name} in {orgs}"

    # 3. Fetch org details
    resp = gitea_client.get_org(org_name)
    assert resp.ok(), f"Get org failed: {resp.status_code} {getattr(resp, 'text', '')}"
    org_info = resp.json
    assert org_info.get("username") == org_name or org_info.get("full_name") == org_name, \
        f"Unexpected org info: {org_info}"

    # 4. Update organization description
    new_description = "Updated org description"
    resp = gitea_client.edit_org(org_name, description=new_description)
    assert resp.ok(), f"Edit org failed: {resp.status_code} {getattr(resp, 'text', '')}"

    # Verify update
    resp = gitea_client.get_org(org_name)
    assert resp.ok(), f"Failed to re-fetch org after edit: {resp.status_code}"
    assert resp.json.get("description") == new_description, \
        f"Org description not updated: {resp.json}"


@pytest.mark.e2e
def test_create_duplicate_org(gitea_client):
    """
    Negative case: creating an organization with the same name twice should fail.
    """

    username = "dup_org_owner"
    email = "dup_org@example.com"
    password = "Password123!"
    org_name = "dup-org"

    # Ensure owner exists
    resp = gitea_client.create_user(username=username, email=email, password=password)
    assert resp.ok() or resp.status_code in (409, 422), \
        f"User creation failed: {resp.status_code} {getattr(resp, 'text', '')}"

    # First creation
    resp = gitea_client.admin_create_org(owner_username=username, org_name=org_name)
    assert resp.ok() or resp.status_code in (409, 422), \
        f"First org creation failed: {resp.status_code} {getattr(resp, 'text', '')}"

    # Second creation should fail
    resp = gitea_client.admin_create_org(owner_username=username, org_name=org_name)
    assert not resp.ok(), "Expected failure for duplicate org creation"
    assert resp.status_code in (409, 422), \
        f"Expected 409/422, got {resp.status_code} {getattr(resp, 'text', '')}"
