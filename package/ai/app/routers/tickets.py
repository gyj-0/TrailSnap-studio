"""票据识别路由"""
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel, Field

from app.services.ticket_service import ticket_service
from app.core.logger import get_logger

logger = get_logger("tickets_router")
router = APIRouter()


class TicketFieldItem(BaseModel):
    """票据字段项"""
    name: str = Field(..., description="字段名称")
    value: str = Field(..., description="字段值")
    confidence: float = Field(..., description="识别置信度", ge=0, le=1)


class TicketResponse(BaseModel):
    """票据识别响应模型"""
    success: bool = Field(..., description="是否成功")
    ticket_type: str = Field("", description="票据类型代码")
    ticket_type_name: str = Field("", description="票据类型名称")
    confidence: float = Field(0.0, description="整体置信度", ge=0, le=1)
    fields: list = Field(default_factory=list, description="识别字段列表")
    raw_text: str = Field("", description="原始 OCR 文本")
    error: Optional[str] = Field(None, description="错误信息")


class TicketTypesResponse(BaseModel):
    """票据类型列表响应"""
    types: dict = Field(default_factory=dict, description="支持的票据类型")


@router.post("/recognize", response_model=TicketResponse)
async def recognize_ticket(
    file: UploadFile = File(..., description="待识别的票据图片"),
    ticket_type: Optional[str] = Form(None, description="票据类型提示 (invoice/receipt/ticket/medical/bank)"),
):
    """识别票据内容
    
    自动检测票据类型并提取关键字段，支持：
    - **invoice**: 增值税发票
    - **receipt**: 通用收据/票据
    - **ticket**: 车票/机票
    - **medical**: 医疗票据
    - **bank**: 银行回单
    - **other**: 其他票据
    
    如不指定 ticket_type，将自动识别票据类型
    """
    logger.info(f"Ticket recognize request: file={file.filename}, type_hint={ticket_type}")
    
    # 验证票据类型
    valid_types = {"invoice", "receipt", "ticket", "medical", "bank", "other", None}
    if ticket_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ticket_type: {ticket_type}. Valid types: {valid_types - {None}}"
        )
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp", "image/gif", "application/pdf"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {allowed_types}"
        )
    
    try:
        image_data = await file.read()
        result = await ticket_service.recognize(image_data, ticket_type=ticket_type)
        return TicketResponse(**result)
    except Exception as e:
        logger.error(f"Ticket recognition error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types", response_model=TicketTypesResponse)
async def get_ticket_types():
    """获取支持的票据类型列表"""
    return TicketTypesResponse(types=ticket_service.TICKET_TYPES)


@router.post("/invoice", response_model=TicketResponse)
async def recognize_invoice(
    file: UploadFile = File(..., description="增值税发票图片"),
):
    """专门识别增值税发票
    
    提取发票代码、发票号码、金额、开票日期等关键信息
    """
    logger.info(f"Invoice recognize request: file={file.filename}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        result = await ticket_service.recognize(image_data, ticket_type="invoice")
        return TicketResponse(**result)
    except Exception as e:
        logger.error(f"Invoice recognition error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/receipt", response_model=TicketResponse)
async def recognize_receipt(
    file: UploadFile = File(..., description="收据/票据图片"),
):
    """专门识别通用收据/票据
    
    提取日期、金额、收据编号等关键信息
    """
    logger.info(f"Receipt recognize request: file={file.filename}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        result = await ticket_service.recognize(image_data, ticket_type="receipt")
        return TicketResponse(**result)
    except Exception as e:
        logger.error(f"Receipt recognition error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transport", response_model=TicketResponse)
async def recognize_transport_ticket(
    file: UploadFile = File(..., description="车票/机票图片"),
):
    """专门识别交通票据
    
    提取票号、日期、出发地、目的地、票价等关键信息
    """
    logger.info(f"Transport ticket recognize request: file={file.filename}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        result = await ticket_service.recognize(image_data, ticket_type="ticket")
        return TicketResponse(**result)
    except Exception as e:
        logger.error(f"Transport ticket recognition error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/medical", response_model=TicketResponse)
async def recognize_medical_ticket(
    file: UploadFile = File(..., description="医疗票据图片"),
):
    """专门识别医疗票据
    
    提取医院名称、日期、金额、医保信息等关键信息
    """
    logger.info(f"Medical ticket recognize request: file={file.filename}")
    
    allowed_types = {"image/jpeg", "image/png", "image/bmp", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        image_data = await file.read()
        result = await ticket_service.recognize(image_data, ticket_type="medical")
        return TicketResponse(**result)
    except Exception as e:
        logger.error(f"Medical ticket recognition error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
