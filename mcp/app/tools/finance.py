"""Tool definitions exposed over mcp.

Each tool is a thin wrapper around one backend endpoint. The docstring
is what a model reads when deciding whether to call the tool, so it
states when the tool is the right choice and what every argument means.
"""

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from app.clients.backend import BackendClient, UpstreamError

mcp = FastMCP("finance-intel")

MAX_LIMIT = 200


def _client() -> BackendClient:
    return BackendClient()


def _fail(exc: UpstreamError) -> dict:
    """Turn an upstream failure into something a model can act on."""
    return {"error": str(exc), "results": [], "count": 0}


@mcp.tool
async def get_transactions(
    account_id: Annotated[
        str | None, Field(description="account uuid, omit to search every account")
    ] = None,
    date_after: Annotated[
        str | None, Field(description="earliest booking date, ISO format")
    ] = None,
    date_before: Annotated[
        str | None, Field(description="latest booking date, ISO format")
    ] = None,
    category: Annotated[
        str | None,
        Field(description="category slug such as groceries, rent or subscription"),
    ] = None,
    amount_min: Annotated[
        float | None, Field(description="smallest transaction amount to include")
    ] = None,
    amount_max: Annotated[
        float | None, Field(description="largest transaction amount to include")
    ] = None,
    search: Annotated[
        str | None, Field(description="free text matched against the statement text")
    ] = None,
    limit: Annotated[int, Field(description="how many rows to return", ge=1)] = 50,
) -> dict:
    """List individual transactions.

    Use this when the question is about specific movements: what was
    spent at a merchant, everything in a date range, the largest charges,
    or anything that needs the raw rows rather than a total. For totals
    per category prefer get_account_summary.
    """
    try:
        payload = await _client().list_transactions(
            account=account_id,
            date_after=date_after,
            date_before=date_before,
            category=category,
            amount_min=amount_min,
            amount_max=amount_max,
            search=search,
            page_size=min(limit, MAX_LIMIT),
        )
    except UpstreamError as exc:
        return _fail(exc)
    return {"count": payload["count"], "results": payload["results"]}


@mcp.tool
async def get_account_summary(
    account_id: Annotated[str, Field(description="account uuid to summarise")],
) -> dict:
    """Report totals and the spending breakdown for one account.

    Use this for questions about how much was spent in total, how income
    compares with expense, which categories dominate, or what share a
    category takes. It answers without pulling individual transactions.
    """
    try:
        return await _client().account_summary(account_id)
    except UpstreamError as exc:
        return {"error": str(exc)}


@mcp.tool
async def get_subscriptions(
    account_id: Annotated[
        str, Field(description="account uuid whose recurring charges are wanted")
    ],
) -> dict:
    """List recurring charges detected for an account.

    Use this for questions about subscriptions, memberships or any
    payment that repeats every month, including what they cost in total
    and when each was last seen.
    """
    try:
        return await _client().account_subscriptions(account_id)
    except UpstreamError as exc:
        return _fail(exc)


@mcp.tool
async def get_anomalies(
    account_id: Annotated[str, Field(description="account uuid to inspect")],
    kind: Annotated[
        str | None,
        Field(
            description=(
                "narrow to one kind: amount_spike, duplicate, "
                "unusual_merchant or off_schedule"
            )
        ),
    ] = None,
) -> dict:
    """List transactions flagged as unusual for an account.

    Use this when the question is about strange, unexpected or suspicious
    activity, duplicate charges, or a payment that looks out of line with
    the usual pattern.
    """
    try:
        return await _client().account_anomalies(account_id, kind)
    except UpstreamError as exc:
        return _fail(exc)


@mcp.tool
async def get_forecast(
    account_id: Annotated[str, Field(description="account uuid to project")],
    horizon_days: Annotated[
        int, Field(description="how many days ahead to project", ge=1, le=365)
    ] = 30,
) -> dict:
    """Project the cash flow of an account into the future.

    Use this for questions about what the balance will look like, whether
    money will run out, or how much is expected to come in and go out
    over the coming days.
    """
    try:
        return await _client().account_forecast(account_id, horizon_days)
    except UpstreamError as exc:
        return {"error": str(exc)}


@mcp.tool
async def search_merchants(
    query: Annotated[
        str, Field(description="part of a merchant name, case insensitive")
    ],
    limit: Annotated[int, Field(description="how many rows to return", ge=1)] = 20,
) -> dict:
    """Find merchants by name.

    Use this to resolve a rough name a person used into the merchant the
    statement actually records, before asking for that merchant's
    transactions.
    """
    try:
        payload = await _client().list_merchants(
            search=query, page_size=min(limit, MAX_LIMIT)
        )
    except UpstreamError as exc:
        return _fail(exc)
    return {"count": payload["count"], "results": payload["results"]}


@mcp.tool
async def list_accounts() -> dict:
    """List the accounts available on the platform.

    Use this first when no account id is known, so a later call can be
    made against the right account.
    """
    try:
        payload = await _client().list_accounts()
    except UpstreamError as exc:
        return _fail(exc)
    return {"count": payload["count"], "results": payload["results"]}
