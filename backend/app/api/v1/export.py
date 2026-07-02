"""
Export API Routes — handles downloads of compiled GTM launch packages as PDF, Word, HTML, Markdown, CSV, and Certificates.
"""
import uuid
import io
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.guards import get_current_active_user
from app.database import get_db
from app.models.user import User
from app.services.event_service import EventService
from app.services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["Export & Integrations"])

VALID_MCP_ACTIONS = {"docs", "calendar", "gmail"}


@router.get(
    "/{event_id}/json",
    summary="Download the full GTM package as JSON",
)
async def export_json(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    service = EventService(db)
    return await service.compile_export_package(event_id, current_user.id)


@router.get(
    "/{event_id}/pdf",
    summary="Download the GTM package as a beautiful PDF booklet",
)
async def export_pdf(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = EventService(db)
    package = await service.compile_export_package(event_id, current_user.id)
    
    pdf_buffer = ExportService.generate_pdf(package)
    filename = f"{package.get('theme', 'hackathon').replace(' ', '_')}_gtm_package.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/{event_id}/docx",
    summary="Download the GTM package as a Word (.docx) document",
)
async def export_docx(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = EventService(db)
    package = await service.compile_export_package(event_id, current_user.id)
    
    docx_buffer = ExportService.generate_docx(package)
    filename = f"{package.get('theme', 'hackathon').replace(' ', '_')}_gtm_package.docx"
    
    return StreamingResponse(
        docx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/{event_id}/markdown",
    summary="Download the GTM package as raw Markdown (.md)",
)
async def export_markdown(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = EventService(db)
    package = await service.compile_export_package(event_id, current_user.id)
    
    md_content = ExportService.generate_markdown(package)
    filename = f"{package.get('theme', 'hackathon').replace(' ', '_')}_gtm_package.md"
    
    return StreamingResponse(
        io.BytesIO(md_content.encode("utf-8")),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/{event_id}/html",
    summary="Download GTM package as formatted HTML webpage",
)
async def export_html(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = EventService(db)
    package = await service.compile_export_package(event_id, current_user.id)
    
    html_content = ExportService.generate_html(package)
    filename = f"{package.get('theme', 'hackathon').replace(' ', '_')}_gtm_package.html"
    
    return StreamingResponse(
        io.BytesIO(html_content.encode("utf-8")),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/{event_id}/csv",
    summary="Download the GTM schedule and timetable as a CSV sheet",
)
async def export_csv(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = EventService(db)
    package = await service.compile_export_package(event_id, current_user.id)
    
    csv_content = ExportService.generate_csv(package)
    filename = f"{package.get('theme', 'hackathon').replace(' ', '_')}_schedule.csv"
    
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/{event_id}/certificate",
    summary="Generate and download a beautiful award certificate PDF",
)
async def export_certificate(
    event_id: uuid.UUID,
    recipient_name: str = "Hackathon Competitor",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = EventService(db)
    package = await service.compile_export_package(event_id, current_user.id)
    gtm = package.get("gtm_package", {})
    brand = gtm.get("brand", {})
    event_name = brand.get("event_name") or package.get("theme") or "GTM Launch Event"
    
    cert_buffer = ExportService.generate_certificate(event_name, recipient_name=recipient_name)
    filename = f"award_certificate_{recipient_name.replace(' ', '_')}.pdf"
    
    return StreamingResponse(
        cert_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post(
    "/{event_id}/{action_type}",
    summary="Sync GTM package to Google Workspace via MCP (docs | calendar | gmail)",
)
async def trigger_mcp_export(
    event_id: uuid.UUID,
    action_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    if action_type not in VALID_MCP_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action. Must be one of: {', '.join(VALID_MCP_ACTIONS)}",
        )

    service = EventService(db)
    return await service.trigger_mcp_action(event_id, current_user.id, action_type)
