from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, validator, root_validator
from enum import Enum
import uuid
import os

from ..utils.supabase_client import get_supabase_client
from ..utils.external_tools import check_calendar_availability, create_calendar_event, update_calendar_event, cancel_calendar_event, send_email
from ..utils.notification_service import create_notification, create_notification_for_admins
from ..utils.redis_client import publish_analytics_event
from ..utils.limiter import limiter

router = APIRouter(prefix="/appointments", tags=["appointments"])


class AppointmentSlot(BaseModel):
    start_time: str
    end_time: str
    duration_minutes: int = 60
    available: bool = True


class AppointmentTypeEnum(str, Enum):
    strategy_session = "strategy_session"
    discovery_call = "discovery_call"
    consultation = "consultation"


class AppointmentBookingRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    company: Optional[str] = None
    start_time: str
    end_time: str
    appointment_type: AppointmentTypeEnum  # strategy_session, discovery_call, consultation
    notes: Optional[str] = None
    timezone: str = "UTC"

    @validator('name')
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) > 120:
            raise ValueError("name must be 1-120 characters")
        return v

    @validator('phone')
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if len(v) > 50:
            raise ValueError("phone is too long")
        return v

    @validator('company')
    def validate_company(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) > 120:
            raise ValueError("company is too long")
        return v

    @validator('notes')
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) > 2000:
            raise ValueError("notes too long")
        return v

    @validator('start_time', 'end_time')
    def validate_iso_dt(cls, v: str) -> str:
        try:
            _ = datetime.fromisoformat(v.replace('Z', '+00:00'))
        except Exception:
            raise ValueError("Invalid ISO datetime")
        return v

    @root_validator(skip_on_failure=True)
    def validate_time_order_and_duration(cls, values):
        st = values.get('start_time')
        et = values.get('end_time')
        if st and et:
            s = datetime.fromisoformat(st.replace('Z', '+00:00'))
            e = datetime.fromisoformat(et.replace('Z', '+00:00'))
            if e <= s:
                raise ValueError("end_time must be after start_time")
            minutes = int((e - s).total_seconds() // 60)
            if minutes != 60:
                raise ValueError("Appointment duration must be 60 minutes")
        return values


class AppointmentRescheduleRequest(BaseModel):
    new_start_time: str
    new_end_time: str
    reason: Optional[str] = None

    @validator('new_start_time', 'new_end_time')
    def validate_iso_dt(cls, v: str) -> str:
        try:
            _ = datetime.fromisoformat(v.replace('Z', '+00:00'))
        except Exception:
            raise ValueError("Invalid ISO datetime")
        return v

    @root_validator(skip_on_failure=True)
    def validate_time_order_and_duration(cls, values):
        st = values.get('new_start_time')
        et = values.get('new_end_time')
        if st and et:
            s = datetime.fromisoformat(st.replace('Z', '+00:00'))
            e = datetime.fromisoformat(et.replace('Z', '+00:00'))
            if e <= s:
                raise ValueError("new_end_time must be after new_start_time")
            minutes = int((e - s).total_seconds() // 60)
            if minutes != 60:
                raise ValueError("Appointment duration must be 60 minutes")
        return values


class AppointmentCancelRequest(BaseModel):
    reason: Optional[str] = None


def require_api_key(request: Request):
    api_key = os.environ.get("BACKEND_API_KEY")
    if api_key:
        provided = request.headers.get("X-API-Key")
        if provided != api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@router.get("/availability")
async def get_availability(
    date: str,  # YYYY-MM-DD format
    duration: int = 60,  # minutes
    timezone: str = "UTC"
):
    """Get available appointment slots for a specific date."""
    try:
        # Parse the date
        date_obj = datetime.fromisoformat(date)
        
        # Define business hours (9 AM to 5 PM)
        start_time = date_obj.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = date_obj.replace(hour=17, minute=0, second=0, microsecond=0)
        
        # Check calendar availability
        availability_result = await check_calendar_availability(
            start_time.isoformat() + "Z",
            end_time.isoformat() + "Z",
            timezone
        )
        
        if not availability_result.get("success"):
            # Return mock slots as fallback
            slots = []
            current_time = start_time
            while current_time < end_time:
                slot_end = current_time + timedelta(minutes=duration)
                if slot_end <= end_time:
                    slots.append(AppointmentSlot(
                        start_time=current_time.isoformat(),
                        end_time=slot_end.isoformat(),
                        duration_minutes=duration,
                        available=True
                    ))
                current_time += timedelta(minutes=duration)
            
            return {
                "success": True,
                "date": date,
                "timezone": timezone,
                "slots": [slot.dict() for slot in slots]
            }
        
        # Process available slots from calendar
        free_slots = availability_result.get("data", {}).get("available_slots", [])
        slots = []
        
        for free_slot in free_slots:
            slot_start = datetime.fromisoformat(free_slot["start"].replace('Z', '+00:00'))
            slot_end = datetime.fromisoformat(free_slot["end"].replace('Z', '+00:00'))
            
            # Split free slot into duration-minute chunks
            current_time = slot_start
            while current_time + timedelta(minutes=duration) <= slot_end:
                chunk_end = current_time + timedelta(minutes=duration)
                slots.append(AppointmentSlot(
                    start_time=current_time.isoformat(),
                    end_time=chunk_end.isoformat(),
                    duration_minutes=duration,
                    available=True
                ))
                current_time = chunk_end
        
        return {
            "success": True,
            "date": date,
            "timezone": timezone,
            "slots": [slot.dict() for slot in slots]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch availability: {str(e)}")


@router.post("/book")
@limiter.limit("10/minute")
async def book_appointment(request: Request, booking_data: AppointmentBookingRequest):
    """Book a new appointment."""
    appointment_id = str(uuid.uuid4())
    
    try:
        # Parse times and check conflicts
        start_dt = datetime.fromisoformat(booking_data.start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(booking_data.end_time.replace('Z', '+00:00'))

        # Check for existing overlapping appointments (scheduled/rescheduled)
        sb = get_supabase_client()
        try:
            existing_result = sb.table("appointments").select("*").in_("status", ["scheduled", "rescheduled"]).execute()
            existing = existing_result.data or []
            for appt in existing:
                try:
                    es = datetime.fromisoformat(str(appt.get("start_time", "")).replace('Z', '+00:00'))
                    ee = datetime.fromisoformat(str(appt.get("end_time", "")).replace('Z', '+00:00'))
                except Exception:
                    continue
                # Overlap if existing_start < new_end and existing_end > new_start
                if es < end_dt and ee > start_dt:
                    raise HTTPException(status_code=409, detail="Requested time conflicts with an existing appointment")
        except HTTPException:
            raise
        except Exception:
            # If conflict check fails due to DB issues, continue (do not block booking)
            pass

        # Create calendar event
        summary = f"{booking_data.appointment_type.replace('_', ' ').title()} - {booking_data.name}"
        description = f"""
Appointment Details:
- Type: {booking_data.appointment_type}
- Name: {booking_data.name}
- Email: {booking_data.email}
- Phone: {booking_data.phone}
- Company: {booking_data.company or 'N/A'}
- Notes: {booking_data.notes or 'None'}
        """
        
        calendar_result = await create_calendar_event(
            summary=summary,
            start_time=booking_data.start_time,
            end_time=booking_data.end_time,
            attendees=[booking_data.email],
            description=description
        )
        
        calendar_event_id = None
        if calendar_result.get("success"):
            calendar_event_id = calendar_result.get("data", {}).get("event_id")
        
        # Store appointment in database
        sb = get_supabase_client()
        appointment_data = {
            "id": appointment_id,
            "name": booking_data.name,
            "email": booking_data.email,
            "phone": booking_data.phone,
            "company": booking_data.company,
            "start_time": booking_data.start_time,
            "end_time": booking_data.end_time,
            "appointment_type": booking_data.appointment_type,
            "notes": booking_data.notes,
            "timezone": booking_data.timezone,
            "status": "scheduled",
            "calendar_event_id": calendar_event_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        sb.table("appointments").insert(appointment_data).execute()
        
        # Send confirmation email
        try:
            email_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #6366f1;">Appointment Confirmed!</h2>
                <p>Hi {booking_data.name},</p>
                <p>Your appointment has been successfully scheduled.</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Appointment Details:</h3>
                    <p><strong>Type:</strong> {booking_data.appointment_type.replace('_', ' ').title()}</p>
                    <p><strong>Date & Time:</strong> {datetime.fromisoformat(booking_data.start_time.replace('Z', '+00:00')).strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p><strong>Duration:</strong> 60 minutes</p>
                    <p><strong>Timezone:</strong> {booking_data.timezone}</p>
                </div>
                
                <p>A calendar invitation has been sent to your email.</p>
                <p>We're looking forward to speaking with you!</p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #6b7280;">
                    Need to reschedule? <a href="https://pixelcraft.lovable.app/#/dashboard/appointments/{appointment_id}">Manage your appointment</a>
                </p>
                
                <p style="font-size: 12px; color: #9ca3af;">
                    PixelCraft Digital Marketing<br>
                    Professional Digital Solutions
                </p>
            </body>
            </html>
            """
            
            await send_email(
                to_email=booking_data.email,
                subject=f"Appointment Confirmed - {booking_data.appointment_type.replace('_', ' ').title()}",
                html_content=email_html
            )
        except Exception as e:
            print(f"Failed to send confirmation email: {e}")
        
        # Create notification for admins
        try:
            await create_notification_for_admins(
                notification_type="appointment",
                severity="info",
                title="New Appointment Booked",
                message=f"{booking_data.name} booked a {booking_data.appointment_type} appointment",
                action_url=f"/dashboard/appointments/{appointment_id}",
                metadata={"appointment_id": appointment_id, "type": booking_data.appointment_type}
            )
        except Exception:
            pass
        
        # Publish analytics event
        try:
            publish_analytics_event("analytics:appointments", "appointment_booked", {
                "appointment_id": appointment_id,
                "type": booking_data.appointment_type
            })
        except Exception:
            pass
        
        return {
            "success": True,
            "appointment_id": appointment_id,
            "message": "Appointment booked successfully",
            "calendar_event_id": calendar_event_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error booking appointment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to book appointment: {str(e)}")


@router.get("/{appointment_id}")
async def get_appointment(appointment_id: str):
    """Get appointment details."""
    try:
        sb = get_supabase_client()
        result = sb.table("appointments").select("*").eq("id", appointment_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "success": True,
            "appointment": result.data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch appointment: {str(e)}")


@router.get("")
async def list_appointments(
    status: Optional[str] = None,
    email: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List appointments with optional filters."""
    try:
        sb = get_supabase_client()
        query = sb.table("appointments").select("*", count="exact")
        
        if status:
            query = query.eq("status", status)
        if email:
            query = query.eq("email", email)
        
        query = query.order("start_time", desc=False).limit(limit).offset(offset)
        result = query.execute()
        
        return {
            "success": True,
            "appointments": result.data or [],
            "total": result.count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list appointments: {str(e)}")


@router.patch("/{appointment_id}/reschedule")
@limiter.limit("10/minute")
async def reschedule_appointment(appointment_id: str, request: AppointmentRescheduleRequest, _: bool = Depends(require_api_key)):
    """Reschedule an existing appointment."""
    try:
        sb = get_supabase_client()
        
        # Get existing appointment
        result = sb.table("appointments").select("*").eq("id", appointment_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        appointment = result.data
        
        # Update calendar event if it exists
        if appointment.get("calendar_event_id"):
            try:
                await update_calendar_event(
                    event_id=appointment["calendar_event_id"],
                    updates={
                        "start": {"dateTime": request.new_start_time, "timeZone": "UTC"},
                        "end": {"dateTime": request.new_end_time, "timeZone": "UTC"}
                    }
                )
            except Exception as e:
                print(f"Failed to update calendar event: {e}")
        
        # Update appointment in database
        sb.table("appointments").update({
            "start_time": request.new_start_time,
            "end_time": request.new_end_time,
            "status": "rescheduled",
            "metadata": {
                "reschedule_reason": request.reason,
                "previous_start": appointment["start_time"]
            }
        }).eq("id", appointment_id).execute()
        
        # Send email notification
        try:
            email_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Appointment Rescheduled</h2>
                <p>Hi {appointment['name']},</p>
                <p>Your appointment has been rescheduled.</p>
                <p><strong>New Date & Time:</strong> {datetime.fromisoformat(request.new_start_time.replace('Z', '+00:00')).strftime('%B %d, %Y at %I:%M %p')}</p>
                <p>A calendar update has been sent to your email.</p>
            </body>
            </html>
            """
            
            await send_email(
                to_email=appointment["email"],
                subject="Appointment Rescheduled",
                html_content=email_html
            )
        except Exception as e:
            print(f"Failed to send reschedule email: {e}")
        
        return {
            "success": True,
            "message": "Appointment rescheduled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reschedule appointment: {str(e)}")


@router.patch("/{appointment_id}/cancel")
@limiter.limit("10/minute")
async def cancel_appointment(appointment_id: str, request: AppointmentCancelRequest, _: bool = Depends(require_api_key)):
    """Cancel an appointment."""
    try:
        sb = get_supabase_client()
        
        # Get existing appointment
        result = sb.table("appointments").select("*").eq("id", appointment_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        appointment = result.data
        
        # Cancel calendar event if it exists
        if appointment.get("calendar_event_id"):
            try:
                await cancel_calendar_event(appointment["calendar_event_id"])
            except Exception as e:
                print(f"Failed to cancel calendar event: {e}")
        
        # Update appointment status
        sb.table("appointments").update({
            "status": "cancelled",
            "metadata": {"cancellation_reason": request.reason}
        }).eq("id", appointment_id).execute()
        
        # Send cancellation email
        try:
            email_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Appointment Cancelled</h2>
                <p>Hi {appointment['name']},</p>
                <p>Your appointment scheduled for {datetime.fromisoformat(appointment['start_time'].replace('Z', '+00:00')).strftime('%B %d, %Y at %I:%M %p')} has been cancelled.</p>
                <p>If you'd like to reschedule, please visit our booking page.</p>
            </body>
            </html>
            """
            
            await send_email(
                to_email=appointment["email"],
                subject="Appointment Cancelled",
                html_content=email_html
            )
        except Exception as e:
            print(f"Failed to send cancellation email: {e}")
        
        return {
            "success": True,
            "message": "Appointment cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel appointment: {str(e)}")
