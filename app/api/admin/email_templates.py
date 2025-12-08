"""
Admin API endpoints for managing email templates
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.db.session import get_db
from app.db.models import EmailTemplate
from app.schemas import EmailTemplateCreate, EmailTemplateUpdate, EmailTemplateResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/admin/email-templates", tags=["admin-email-templates"])


@router.get("", response_model=List[EmailTemplateResponse])
async def list_templates(
    audience_type: Optional[str] = Query(None, description="Filter by audience type"),
    active_only: bool = Query(True, description="Show only active templates"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all email templates."""
    query = select(EmailTemplate)

    if audience_type:
        query = query.where(EmailTemplate.audience_type == audience_type)

    if active_only:
        query = query.where(EmailTemplate.is_active == True)

    result = await db.execute(query)
    templates = result.scalars().all()

    return templates


@router.get("/{template_id}", response_model=EmailTemplateResponse)
async def get_template(
    template_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific email template by ID."""
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.post("", response_model=EmailTemplateResponse)
async def create_template(
    template: EmailTemplateCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new email template."""
    # If this is set as default, unset others for the same audience type
    if template.is_default and template.audience_type:
        await db.execute(
            select(EmailTemplate)
            .where(EmailTemplate.audience_type == template.audience_type)
            .where(EmailTemplate.is_default == True)
            .values(is_default=False)
        )
        await db.commit()

    db_template = EmailTemplate(
        **template.dict(),
        version=1
    )

    db.add(db_template)
    await db.commit()
    await db.refresh(db_template)

    return db_template


@router.put("/{template_id}", response_model=EmailTemplateResponse)
async def update_template(
    template_id: int,
    template_update: EmailTemplateUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an email template."""
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # If setting as default, unset others for the same audience type
    if template_update.is_default and template_update.audience_type != template.audience_type:
        # Changing audience type and setting as default
        await db.execute(
            select(EmailTemplate)
            .where(EmailTemplate.audience_type == template.audience_type)
            .where(EmailTemplate.is_default == True)
            .values(is_default=False)
        )
    elif template_update.is_default and template.audience_type:
        # Setting as default for same audience type
        await db.execute(
            select(EmailTemplate)
            .where(EmailTemplate.audience_type == template.audience_type)
            .where(EmailTemplate.id != template_id)
            .where(EmailTemplate.is_default == True)
            .values(is_default=False)
        )

    # Update fields
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    # Increment version on update
    template.version += 1

    await db.commit()
    await db.refresh(template)

    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an email template (soft delete - sets is_active to false)."""
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.is_active = False
    await db.commit()

    return {"message": "Template deleted successfully"}


@router.get("/preview/{template_id}")
async def preview_template(
    template_id: int,
    first_name: Optional[str] = Query(None, description="Preview with first name"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Preview an email template with variables rendered."""
    result = await db.execute(
        select(EmailTemplate).where(EmailTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Render variables
    variables = {
        "first_name": first_name or "there",
        "signup_date": "today",
        "unsubscribe_url": "https://blitz.ws/unsubscribe"
    }

    rendered_subject = template.subject
    rendered_html = template.html_content
    rendered_text = template.text_content or ""

    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        rendered_subject = rendered_subject.replace(placeholder, str(value))
        rendered_html = rendered_html.replace(placeholder, str(value))
        rendered_text = rendered_text.replace(placeholder, str(value))

    return {
        "subject": rendered_subject,
        "html_content": rendered_html,
        "text_content": rendered_text
    }
