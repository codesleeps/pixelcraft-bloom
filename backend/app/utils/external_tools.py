import httpx
import asyncio
import logging
import json
import datetime
from typing import Optional, Dict, Any, List
from ..config import settings

logger = logging.getLogger("pixelcraft.external_tools")


async def _make_api_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    json_data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """Helper function to make API requests with retry logic and error handling."""
    timeout = httpx.Timeout(30.0)
    retries = 0
    backoff = 1  # Initial backoff in seconds

    while retries <= max_retries:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.debug(f"Making {method} request to {url} with params {params} and data {json_data}")
                response = await client.request(method, url, headers=headers, json=json_data, params=params)
                logger.debug(f"Response status: {response.status_code}, body: {response.text}")

                if response.status_code >= 200 and response.status_code < 300:
                    return response.json()
                elif response.status_code >= 400 and response.status_code < 500:
                    # Client errors, raise exception
                    raise httpx.HTTPError(f"Client error: {response.status_code} - {response.text}", request=response.request, response=response)
                elif response.status_code >= 500 or response.status_code == 429:
                    # Server errors or rate limit, retry
                    if retries < max_retries:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        retries += 1
                        continue
                    else:
                        raise httpx.HTTPError(f"Server error after retries: {response.status_code} - {response.text}", request=response.request, response=response)
                else:
                    raise httpx.HTTPError(f"Unexpected status: {response.status_code} - {response.text}", request=response.request, response=response)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            if retries < max_retries:
                await asyncio.sleep(backoff)
                backoff *= 2
                retries += 1
                continue
            else:
                raise e
    raise Exception("Max retries exceeded")


# CRM Tools (HubSpot)

async def create_crm_contact(
    email: str,
    first_name: str,
    last_name: str,
    company: str,
    phone: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    if not settings.crm:
        return {"error": "CRM not configured", "skipped": True}

    properties = {
        "email": email,
        "firstname": first_name,
        "lastname": last_name,
        "company": company,
    }
    if phone:
        properties["phone"] = phone
    if metadata:
        properties.update(metadata)

    payload = {"properties": properties}
    url = f"{settings.crm.api_url}/crm/v3/objects/contacts"
    headers = {"Authorization": f"Bearer {settings.crm.api_key}"}

    try:
        response = await _make_api_request("POST", url, headers, json_data=payload)
        return {"contact_id": response["id"], "status": "created"}
    except httpx.HTTPError as e:
        if e.response and e.response.status_code == 409:
            # Duplicate, try to find existing
            try:
                search_result = await _search_crm_contact_by_email(email)
                if search_result.get("results"):
                    return {"contact_id": search_result["results"][0]["id"], "status": "existing"}
            except Exception:
                pass
        logger.error(f"Error creating CRM contact: {e}")
        return {"error": str(e), "status_code": getattr(e.response, 'status_code', None), "details": {}}
    except Exception as e:
        logger.error(f"Error creating CRM contact: {e}")
        return {"error": str(e), "status_code": None, "details": {}}


async def _search_crm_contact_by_email(email: str) -> Dict[str, Any]:
    """Helper to search for contact by email."""
    url = f"{settings.crm.api_url}/crm/v3/objects/contacts/search"
    headers = {"Authorization": f"Bearer {settings.crm.api_key}"}
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email
            }]
        }]
    }
    return await _make_api_request("POST", url, headers, json_data=payload)


async def update_crm_contact(contact_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    if not settings.crm:
        return {"error": "CRM not configured", "skipped": True}

    payload = {"properties": properties}
    url = f"{settings.crm.api_url}/crm/v3/objects/contacts/{contact_id}"
    headers = {"Authorization": f"Bearer {settings.crm.api_key}"}

    try:
        response = await _make_api_request("PATCH", url, headers, json_data=payload)
        return {"contact_id": contact_id, "updated_properties": properties, "status": "updated"}
    except Exception as e:
        logger.error(f"Error updating CRM contact: {e}")
        return {"error": str(e), "status_code": getattr(e.response, 'status_code', None), "details": {}}


async def create_crm_deal(
    contact_id: str,
    deal_name: str,
    amount: float,
    stage: str,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    if not settings.crm:
        return {"error": "CRM not configured", "skipped": True}

    properties = {
        "dealname": deal_name,
        "amount": str(amount),
        "dealstage": stage,
    }
    if metadata:
        properties.update(metadata)

    payload = {
        "properties": properties,
        "associations": [{
            "to": {"id": contact_id},
            "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}]  # Contact to Deal
        }]
    }
    url = f"{settings.crm.api_url}/crm/v3/objects/deals"
    headers = {"Authorization": f"Bearer {settings.crm.api_key}"}

    try:
        response = await _make_api_request("POST", url, headers, json_data=payload)
        return {"deal_id": response["id"], "status": "created"}
    except Exception as e:
        logger.error(f"Error creating CRM deal: {e}")
        return {"error": str(e), "status_code": getattr(e.response, 'status_code', None), "details": {}}


# Email Tools (SendGrid)

async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: Optional[str] = None,
    cc: Optional[List[str]] = None
) -> Dict[str, Any]:
    if not settings.email:
        return {"error": "Email not configured", "skipped": True}

    from_email = from_email or settings.email.from_email
    personalizations = [{"to": [{"email": to_email}]}]
    if cc:
        personalizations[0]["cc"] = [{"email": email} for email in cc]

    payload = {
        "personalizations": personalizations,
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_content}]
    }
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {"Authorization": f"Bearer {settings.email.api_key}"}

    try:
        await _make_api_request("POST", url, headers, json_data=payload)
        return {"message_id": "sent", "status": "sent"}  # SendGrid doesn't return message ID in response
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return {"error": str(e), "status_code": getattr(e.response, 'status_code', None), "details": {}}


async def send_template_email(
    to_email: str,
    template_id: str,
    template_data: Dict[str, Any],
    from_email: Optional[str] = None
) -> Dict[str, Any]:
    if not settings.email:
        return {"error": "Email not configured", "skipped": True}

    from_email = from_email or settings.email.from_email
    payload = {
        "personalizations": [{"to": [{"email": to_email}], "dynamic_template_data": template_data}],
        "from": {"email": from_email},
        "template_id": template_id
    }
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {"Authorization": f"Bearer {settings.email.api_key}"}

    try:
        await _make_api_request("POST", url, headers, json_data=payload)
        return {"message_id": "sent", "status": "sent"}
    except Exception as e:
        logger.error(f"Error sending template email: {e}")
        return {"error": str(e), "status_code": getattr(e.response, 'status_code', None), "details": {}}


# Calendar Tools (Google Calendar)

async def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    attendees: List[str],
    description: Optional[str] = None,
    location: Optional[str] = None
) -> Dict[str, Any]:
    if not settings.calendar:
        return {"error": "Calendar not configured", "skipped": True}

    payload = {
        "summary": summary,
        "start": {"dateTime": start_time, "timeZone": "UTC"},
        "end": {"dateTime": end_time, "timeZone": "UTC"},
        "attendees": [{"email": email} for email in attendees],
    }
    if description:
        payload["description"] = description
    if location:
        payload["location"] = location

    url = f"https://www.googleapis.com/calendar/v3/calendars/{settings.calendar.calendar_id}/events"
    headers = {"Authorization": f"Bearer {settings.calendar.api_key}"}

    try:
        response = await _make_api_request("POST", url, headers, json_data=payload)
        return {"event_id": response["id"], "link": response.get("htmlLink"), "status": "created"}
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        return {"error": str(e), "status_code": getattr(e.response, 'status_code', None), "details": {}}


async def check_calendar_availability(
    start_time: str,
    end_time: str,
    timezone: str = "UTC"
) -> Dict[str, Any]:
    if not settings.calendar:
        return {"error": "Calendar not configured", "skipped": True}

    payload = {
        "timeMin": start_time,
        "timeMax": end_time,
        "timeZone": timezone,
        "items": [{"id": settings.calendar.calendar_id}]
    }
    url = "https://www.googleapis.com/calendar/v3/freeBusy"
    headers = {"Authorization": f"Bearer {settings.calendar.api_key}"}

    try:
        response = await _make_api_request("POST", url, headers, json_data=payload)
        busy_periods = response["calendars"][settings.calendar.calendar_id]["busy"]
        # Compute free slots
        free_slots = []
        current_start = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        current_end = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        for busy in sorted(busy_periods, key=lambda x: x["start"]):
            busy_start = datetime.datetime.fromisoformat(busy["start"].replace('Z', '+00:00'))
            busy_end = datetime.datetime.fromisoformat(busy["end"].replace('Z', '+00:00'))
            if busy_start > current_start:
                free_slots.append({"start": current_start.isoformat(), "end": busy_start.isoformat()})
            current_start = max(current_start, busy_end)
        if current_start < current_end:
            free_slots.append({"start": current_start.isoformat(), "end": current_end.isoformat()})
        return {"available_slots": free_slots}
    except Exception as e:
        logger.error(f"Error checking calendar availability: {e}")
        return {"error": str(e), "status_code": getattr(e.response, 'status_code', None), "details": {}}


async def update_calendar_event(event_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    if not settings.calendar:
        return {"error": "Calendar not configured", "skipped": True}

    url = f"https://www.googleapis.com/calendar/v3/calendars/{settings.calendar.calendar_id}/events/{event_id}"
    headers = {"Authorization": f"Bearer {settings.calendar.api_key}"}

    try:
        response = await _make_api_request("PATCH", url, headers, json_data=updates)
        return {"event_id": event_id, "updated": updates, "status": "updated"}
    except Exception as e:
        logger.error(f"Error updating calendar event: {e}")
        return {"error": str(e), "status_code": getattr(e.response, 'status_code', None), "details": {}}


async def test_external_services() -> Dict[str, bool]:
    result = {}
    if settings.crm:
        try:
            await _make_api_request(
                "GET",
                f"{settings.crm.api_url}/crm/v3/objects/contacts",
                {"Authorization": f"Bearer {settings.crm.api_key}"},
                params={"limit": 1}
            )
            result["crm"] = True
        except Exception:
            result["crm"] = False
    if settings.email:
        try:
            await _make_api_request(
                "GET",
                "https://api.sendgrid.com/v3/user/profile",
                {"Authorization": f"Bearer {settings.email.api_key}"}
            )
            result["email"] = True
        except Exception:
            result["email"] = False
    if settings.calendar:
        try:
            await _make_api_request(
                "GET",
                f"https://www.googleapis.com/calendar/v3/calendars/{settings.calendar.calendar_id}",
                {"Authorization": f"Bearer {settings.calendar.api_key}"}
            )
            result["calendar"] = True
        except Exception:
            result["calendar"] = False
    return result