import pytest
from httpx import AsyncClient

# To make this fully functional, we'd need to mock or ensure a Category exists
# and the user is authenticated. This skeleton demonstrates the structure.

@pytest.mark.asyncio
async def test_create_expense(client: AsyncClient, db_session):
    pass

@pytest.mark.asyncio
async def test_get_expenses_with_filters(client: AsyncClient):
    pass

@pytest.mark.asyncio
async def test_delete_own_expense(client: AsyncClient):
    pass

@pytest.mark.asyncio
async def test_cannot_delete_others_expense(client: AsyncClient):
    pass
