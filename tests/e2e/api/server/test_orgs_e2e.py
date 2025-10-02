import pytest

from clients.http_gitea_client import GiteaHttpClient


@pytest.mark.e2e
def test_org_lifecycle(gitea_client: GiteaHttpClient):
    """
    Full organization lifecycle:
    1. create organization
    2. list orgs for user
    3. fetch org details
    4. update organization description
    5. delete org (not directly supported via API, so skipped if not possible)
    """

    username = "org_owner"
    email = "org_owner@example.com"
    password = "Password123!"
    org_name = "sample-org"

    # Ensure owner user exists
    result = gitea_client.create_user(username=username, email=email, password=password)
    assert result.ok() or result.status == 422, f"User creation failed: {result.status} {result.text}"

    # 1. create organization
    result = gitea_client.admin_create_org(owner_username=username, org_name=org_name, description="Initial org")
    assert result.ok() or result.status == 422, f"Org creation failed: {result.status} {result.text}"
    org_data = result.json()
    assert org_data["username"] == org_name or org_data.get("full_name") == org_name, f"Unexpected org data: {org_data}"

    # 2. list orgs for user
    result = gitea_client.list_orgs()
    assert result.ok(), f"List orgs failed: {result.status} {result.text}"
    orgs = [o.get("username") or o.get("full_name") for o in result.json()]
    assert org_name in orgs, f"Expected {org_name} in {orgs}"

    # 3. fetch org details
    result = gitea_client.get_org(org_name)
    assert result.ok(), f"Get org failed: {result.status} {result.text}"
    org_info = result.json()
    assert org_info["username"] == org_name or org_info.get("full_name") == org_name

    # 4. update organization description
    new_description = "Updated org description"
    result = gitea_client.edit_org(org_name, description=new_description)
    assert result.ok(), f"Edit org failed: {result.status} {result.text}"
    result = gitea_client.get_org(org_name)
    assert result.ok()
    assert result.json()["description"] == new_description, f"Org description not updated: {result.json()}"

    # ⚠️ 5. delete organization – Gitea API often does not allow direct org deletion via API.
    # Якщо треба, можна буде реалізувати через cleanup-скрипт або прямий DB reset у CI.


@pytest.mark.e2e
def test_create_duplicate_org(gitea_client: GiteaHttpClient):
    """
    Negative case: creating an organization with the same name twice should fail.
    """

    username = "dup_org_owner"
    email = "dup_org@example.com"
    password = "Password123!"
    org_name = "dup-org"

    # Ensure owner user exists
    result = gitea_client.create_user(username=username, email=email, password=password)
    assert result.ok() or result.status == 422

    # First creation
    result = gitea_client.admin_create_org(owner_username=username, org_name=org_name)
    assert result.ok() or result.status == 422

    # Second creation should fail
    result = gitea_client.admin_create_org(owner_username=username, org_name=org_name)
    assert not result.ok(), f"Expected failure for duplicate org, got {result.status}"
    assert result.status in (409, 422), f"Expected 409/422, got {result.status} {result.text}"
