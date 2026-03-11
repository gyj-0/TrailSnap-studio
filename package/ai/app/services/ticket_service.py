"""票据识别服务 - 基于 OCR 和规则引擎"""
import io
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from PIL import Image

from app.core.config import settings
from app.core.logger import get_logger
from app.services.ocr_service import ocr_service

logger = get_logger("ticket_service")


@dataclass
class TicketField:
    """票据字段"""
    name: str
    value: str
    confidence: float
    raw_text: str


class TicketService:
    """票据识别服务类
    
    基于 OCR 和规则引擎，提供各类票据的识别和解析
    """
    
    # 票据类型定义
    TICKET_TYPES = {
        "invoice": "增值税发票",
        "receipt": "通用票据",
        "ticket": "车票/机票",
        "medical": "医疗票据",
        "bank": "银行回单",
        "other": "其他票据",
    }
    
    def __init__(self):
        self.ocr_service = ocr_service
    
    async def recognize(
        self,
        image_data: bytes,
        ticket_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """识别票据
        
        Args:
            image_data: 图片二进制数据
            ticket_type: 票据类型提示，None 表示自动识别
        
        Returns:
            票据识别结果
        """
        try:
            # 执行 OCR
            ocr_result = await self.ocr_service.recognize_structure(image_data)
            
            if not ocr_result["success"]:
                return {
                    "success": False,
                    "error": f"OCR failed: {ocr_result.get('error', 'Unknown error')}",
                }
            
            full_text = ocr_result["full_text"]
            lines = ocr_result["lines"]
            
            # 自动检测票据类型
            detected_type = ticket_type or self._detect_ticket_type(full_text, lines)
            
            # 根据票据类型解析
            if detected_type == "invoice":
                fields = self._parse_invoice(lines, full_text)
            elif detected_type == "receipt":
                fields = self._parse_receipt(lines, full_text)
            elif detected_type == "ticket":
                fields = self._parse_transport_ticket(lines, full_text)
            elif detected_type == "medical":
                fields = self._parse_medical_ticket(lines, full_text)
            elif detected_type == "bank":
                fields = self._parse_bank_receipt(lines, full_text)
            else:
                fields = self._extract_common_fields(lines, full_text)
            
            # 计算整体置信度
            avg_confidence = sum(f.confidence for f in fields) / len(fields) if fields else 0.0
            
            return {
                "success": True,
                "ticket_type": detected_type,
                "ticket_type_name": self.TICKET_TYPES.get(detected_type, "未知"),
                "confidence": round(avg_confidence, 4),
                "fields": [
                    {
                        "name": f.name,
                        "value": f.value,
                        "confidence": f.confidence,
                    }
                    for f in fields
                ],
                "raw_text": full_text,
            }
            
        except Exception as e:
            logger.error(f"Ticket recognition failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def _detect_ticket_type(self, full_text: str, lines: List[str]) -> str:
        """检测票据类型
        
        Args:
            full_text: 完整文本
            lines: 行列表
        
        Returns:
            票据类型
        """
        text_lower = full_text.lower()
        
        # 发票关键词
        invoice_keywords = ["发票", "增值税", "专用发票", "普通发票", "发票代码", "发票号码"]
        if any(kw in text_lower for kw in invoice_keywords):
            return "invoice"
        
        # 车票/机票关键词
        ticket_keywords = ["车票", "机票", "登机牌", "航班", "车次", "座位", "出发", "到达"]
        if any(kw in text_lower for kw in ticket_keywords):
            return "ticket"
        
        # 医疗票据关键词
        medical_keywords = ["医院", "门诊", "住院", "医保", "收费", "处方", "病历"]
        if any(kw in text_lower for kw in medical_keywords):
            return "medical"
        
        # 银行回单关键词
        bank_keywords = ["银行", "回单", "转账", "收款", "付款", "交易", "流水号"]
        if any(kw in text_lower for kw in bank_keywords):
            return "bank"
        
        # 通用票据关键词
        receipt_keywords = ["收据", "收款", "金额", "合计", "小写", "大写"]
        if any(kw in text_lower for kw in receipt_keywords):
            return "receipt"
        
        return "other"
    
    def _parse_invoice(self, lines: List[str], full_text: str) -> List[TicketField]:
        """解析增值税发票
        
        Args:
            lines: 文本行
            full_text: 完整文本
        
        Returns:
            字段列表
        """
        fields = []
        
        # 发票代码
        code_match = re.search(r'发票代码[：:]\s*(\d{10,12})', full_text)
        if code_match:
            fields.append(TicketField(
                name="发票代码",
                value=code_match.group(1),
                confidence=0.9,
                raw_text=code_match.group(0)
            ))
        
        # 发票号码
        number_match = re.search(r'发票号码[：:]\s*(\d{8,20})', full_text)
        if number_match:
            fields.append(TicketField(
                name="发票号码",
                value=number_match.group(1),
                confidence=0.9,
                raw_text=number_match.group(0)
            ))
        
        # 开票日期
        date_match = re.search(r'(\d{4}[年/-]\d{1,2}[月/-]\d{1,2})', full_text)
        if date_match:
            fields.append(TicketField(
                name="开票日期",
                value=date_match.group(1),
                confidence=0.85,
                raw_text=date_match.group(0)
            ))
        
        # 金额
        amount_patterns = [
            r'价税合计[（(]大写[)）][^\d]*[\d\s]+(\d+\.?\d*)',
            r'[¥￥]\s*(\d+\.?\d{0,2})',
            r'合计[：:]\s*(\d+\.?\d{0,2})',
        ]
        for pattern in amount_patterns:
            amount_match = re.search(pattern, full_text)
            if amount_match:
                fields.append(TicketField(
                    name="金额",
                    value=amount_match.group(1),
                    confidence=0.8,
                    raw_text=amount_match.group(0)
                ))
                break
        
        # 购买方/销售方
        for i, line in enumerate(lines):
            if "购买方" in line or "购方" in line:
                # 尝试获取下一行的名称
                if i + 1 < len(lines):
                    fields.append(TicketField(
                        name="购买方名称",
                        value=lines[i + 1].strip(),
                        confidence=0.7,
                        raw_text=lines[i + 1]
                    ))
            elif "销售方" in line or "销方" in line:
                if i + 1 < len(lines):
                    fields.append(TicketField(
                        name="销售方名称",
                        value=lines[i + 1].strip(),
                        confidence=0.7,
                        raw_text=lines[i + 1]
                    ))
        
        return fields
    
    def _parse_receipt(self, lines: List[str], full_text: str) -> List[TicketField]:
        """解析通用收据
        
        Args:
            lines: 文本行
            full_text: 完整文本
        
        Returns:
            字段列表
        """
        fields = []
        
        # 收据编号
        receipt_no = re.search(r'No[.．]?\s*[:：]?\s*(\w+)', full_text)
        if receipt_no:
            fields.append(TicketField(
                name="收据编号",
                value=receipt_no.group(1),
                confidence=0.85,
                raw_text=receipt_no.group(0)
            ))
        
        # 日期
        date_match = re.search(r'(\d{4}[年/-]\d{1,2}[月/-]\d{1,2})', full_text)
        if date_match:
            fields.append(TicketField(
                name="日期",
                value=date_match.group(1),
                confidence=0.85,
                raw_text=date_match.group(0)
            ))
        
        # 金额
        amount_match = re.search(r'[¥￥]\s*(\d+\.?\d{0,2})', full_text)
        if amount_match:
            fields.append(TicketField(
                name="金额",
                value=amount_match.group(1),
                confidence=0.85,
                raw_text=amount_match.group(0)
            ))
        
        # 收款事由/项目
        for i, line in enumerate(lines):
            if any(kw in line for kw in ["收款事由", "项目", "内容", "摘要"]):
                if i + 1 < len(lines):
                    fields.append(TicketField(
                        name="收款事由",
                        value=lines[i + 1].strip(),
                        confidence=0.7,
                        raw_text=lines[i + 1]
                    ))
        
        return fields
    
    def _parse_transport_ticket(self, lines: List[str], full_text: str) -> List[TicketField]:
        """解析交通票据
        
        Args:
            lines: 文本行
            full_text: 完整文本
        
        Returns:
            字段列表
        """
        fields = []
        
        # 票号
        ticket_no = re.search(r'(票号|订单号|电子票号)[：:]?\s*(\w+)', full_text)
        if ticket_no:
            fields.append(TicketField(
                name="票号",
                value=ticket_no.group(2),
                confidence=0.85,
                raw_text=ticket_no.group(0)
            ))
        
        # 日期时间
        datetime_match = re.search(
            r'(\d{4}[年/-]\d{1,2}[月/-]\d{1,2})\s*(\d{1,2}[：:]\d{2})?',
            full_text
        )
        if datetime_match:
            fields.append(TicketField(
                name="日期",
                value=datetime_match.group(1),
                confidence=0.85,
                raw_text=datetime_match.group(0)
            ))
        
        # 金额
        amount_match = re.search(r'[¥￥]\s*(\d+\.?\d{0,2})', full_text)
        if amount_match:
            fields.append(TicketField(
                name="票价",
                value=amount_match.group(1),
                confidence=0.85,
                raw_text=amount_match.group(0)
            ))
        
        # 出发地/目的地
        route_match = re.search(r'([^\s]{2,6})[\s]*[-→至到][\s]*([^\s]{2,6})', full_text)
        if route_match:
            fields.append(TicketField(
                name="出发地",
                value=route_match.group(1).strip(),
                confidence=0.75,
                raw_text=route_match.group(0)
            ))
            fields.append(TicketField(
                name="目的地",
                value=route_match.group(2).strip(),
                confidence=0.75,
                raw_text=route_match.group(0)
            ))
        
        # 座位/车次信息
        for i, line in enumerate(lines):
            if any(kw in line for kw in ["车次", "航班", "座位", "舱位"]):
                fields.append(TicketField(
                    name="行程信息",
                    value=line.strip(),
                    confidence=0.7,
                    raw_text=line
                ))
        
        return fields
    
    def _parse_medical_ticket(self, lines: List[str], full_text: str) -> List[TicketField]:
        """解析医疗票据
        
        Args:
            lines: 文本行
            full_text: 完整文本
        
        Returns:
            字段列表
        """
        fields = []
        
        # 医院名称
        for i, line in enumerate(lines[:5]):  # 通常在开头
            if "医院" in line or "诊所" in line or "卫生院" in line:
                fields.append(TicketField(
                    name="医疗机构",
                    value=line.strip(),
                    confidence=0.85,
                    raw_text=line
                ))
                break
        
        # 日期
        date_match = re.search(r'(\d{4}[年/-]\d{1,2}[月/-]\d{1,2})', full_text)
        if date_match:
            fields.append(TicketField(
                name="日期",
                value=date_match.group(1),
                confidence=0.85,
                raw_text=date_match.group(0)
            ))
        
        # 金额
        amount_patterns = [
            r'合计金额[：:]\s*[¥￥]?\s*(\d+\.?\d{0,2})',
            r'总金额[：:]\s*[¥￥]?\s*(\d+\.?\d{0,2})',
            r'[¥￥]\s*(\d+\.?\d{0,2})',
        ]
        for pattern in amount_patterns:
            amount_match = re.search(pattern, full_text)
            if amount_match:
                fields.append(TicketField(
                    name="金额",
                    value=amount_match.group(1),
                    confidence=0.8,
                    raw_text=amount_match.group(0)
                ))
                break
        
        # 医保信息
        if "医保" in full_text or "统筹" in full_text:
            fields.append(TicketField(
                name="医保标识",
                value="是",
                confidence=0.7,
                raw_text="包含医保信息"
            ))
        
        return fields
    
    def _parse_bank_receipt(self, lines: List[str], full_text: str) -> List[TicketField]:
        """解析银行回单
        
        Args:
            lines: 文本行
            full_text: 完整文本
        
        Returns:
            字段列表
        """
        fields = []
        
        # 银行名称
        for line in lines[:5]:
            if "银行" in line:
                fields.append(TicketField(
                    name="银行",
                    value=line.strip(),
                    confidence=0.85,
                    raw_text=line
                ))
                break
        
        # 流水号
        serial_match = re.search(r'(流水号|交易号)[：:]?\s*(\w+)', full_text)
        if serial_match:
            fields.append(TicketField(
                name="流水号",
                value=serial_match.group(2),
                confidence=0.85,
                raw_text=serial_match.group(0)
            ))
        
        # 日期时间
        datetime_match = re.search(
            r'(\d{4}[年/-]\d{1,2}[月/-]\d{1,2})\s*(\d{1,2}[：:]\d{2}[：:]?\d{0,2})?',
            full_text
        )
        if datetime_match:
            fields.append(TicketField(
                name="交易日期",
                value=datetime_match.group(1),
                confidence=0.85,
                raw_text=datetime_match.group(0)
            ))
        
        # 金额
        amount_match = re.search(r'[¥￥]\s*(\d+\.?\d{0,2})', full_text)
        if amount_match:
            fields.append(TicketField(
                name="交易金额",
                value=amount_match.group(1),
                confidence=0.85,
                raw_text=amount_match.group(0)
            ))
        
        # 交易类型
        for i, line in enumerate(lines):
            if any(kw in line for kw in ["转账", "收款", "付款", "存款", "取款"]):
                fields.append(TicketField(
                    name="交易类型",
                    value=line.strip(),
                    confidence=0.7,
                    raw_text=line
                ))
                break
        
        return fields
    
    def _extract_common_fields(self, lines: List[str], full_text: str) -> List[TicketField]:
        """提取通用字段
        
        Args:
            lines: 文本行
            full_text: 完整文本
        
        Returns:
            字段列表
        """
        fields = []
        
        # 日期
        date_match = re.search(r'(\d{4}[年/-]\d{1,2}[月/-]\d{1,2})', full_text)
        if date_match:
            fields.append(TicketField(
                name="日期",
                value=date_match.group(1),
                confidence=0.7,
                raw_text=date_match.group(0)
            ))
        
        # 金额
        amount_match = re.search(r'[¥￥]\s*(\d+\.?\d{0,2})', full_text)
        if amount_match:
            fields.append(TicketField(
                name="金额",
                value=amount_match.group(1),
                confidence=0.7,
                raw_text=amount_match.group(0)
            ))
        
        # 编号
        no_match = re.search(r'(No|编号|号码)[.．]?\s*[:：]?\s*(\w+)', full_text)
        if no_match:
            fields.append(TicketField(
                name="编号",
                value=no_match.group(2),
                confidence=0.6,
                raw_text=no_match.group(0)
            ))
        
        return fields


# 全局票据识别服务实例
ticket_service = TicketService()
