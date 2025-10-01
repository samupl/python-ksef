"""Tests for searching invoices."""

import pytest

from ksef.client import Client


@pytest.mark.integration()
@pytest.mark.withoutresponses()
def test_search_invoices(client: Client) -> None:
    """Integration test for searching invoices."""
    invoices = client.search_invoices()
    raise Exception(invoices)
