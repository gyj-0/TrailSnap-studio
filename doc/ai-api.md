# TrailSnap AI 服务接口文档

## 基础信息

- **Base URL**: `http://localhost:8001`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式

### 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": { }
}
```

### 错误响应

```json
{
  "code": 500,
  "message": "错误描述",
  "detail": "详细错误信息"
}
```

## OCR 模块

### 1. 通用文字识别

识别图片中的文字内容。

**POST** `/ocr/recognize`

#### 请求参数

Content-Type: `multipart/form-data` 或 `application/json`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是* | 图片文件（与 url 二选一） |
| url | string | 是* | 图片 URL（与 file 二选一） |
| language | string | 否 | 识别语言，默认 `ch`（中文） |
| use_gpu | bool | 否 | 是否使用 GPU，默认 `auto` |

**支持的语言**:
- `ch` / `ch_sim` - 简体中文
- `ch_tra` - 繁体中文
- `en` - 英文
- `japan` - 日文
- `korean` - 韩文
- `latin` - 拉丁文

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "text": "昆明站\nG1234\n北京南\n2024年02月10日\n08:00开",
    "regions": [
      {
        "text": "昆明站",
        "confidence": 0.9876,
        "bbox": [[120, 80], [280, 80], [280, 140], [120, 140]],
        "center": [200, 110]
      },
      {
        "text": "G1234",
        "confidence": 0.9923,
        "bbox": [[300, 200], [450, 200], [450, 260], [300, 260]],
        "center": [375, 230]
      }
    ],
    "elapsed": 0.523
  }
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| text | string | 所有识别文本的拼接 |
| regions | array | 每个文本区域的识别结果 |
| regions[].text | string | 区域文本内容 |
| regions[].confidence | float | 置信度，范围 0-1 |
| regions[].bbox | array | 四边形边界框坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] |
| regions[].center | array | 区域中心点坐标 [x, y] |
| elapsed | float | 处理耗时（秒） |

### 2. 文本检测

仅检测图片中的文本区域，不识别文字内容。

**POST** `/ocr/detect`

#### 请求参数

与 `/ocr/recognize` 相同。

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "regions": [
      {
        "bbox": [[120, 80], [280, 80], [280, 140], [120, 140]],
        "center": [200, 110],
        "score": 0.95
      }
    ],
    "count": 8,
    "elapsed": 0.234
  }
}
```

### 3. 结构化 OCR

识别并结构化输出表格、票据等文档。

**POST** `/ocr/structure`

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是* | 图片文件 |
| url | string | 是* | 图片 URL |
| doc_type | string | 否 | 文档类型: `general`, `table`, `receipt` |

#### 响应示例（表格）

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "doc_type": "table",
    "html": "<table>...</table>",
    "cells": [
      {
        "row": 0,
        "col": 0,
        "text": "项目",
        "bbox": [[10, 10], [100, 10], [100, 50], [10, 50]]
      }
    ],
    "elapsed": 1.234
  }
}
```

## 人脸识别模块

### 1. 人脸检测

检测图片中的人脸位置和属性。

**POST** `/face/detect`

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是* | 图片文件 |
| url | string | 是* | 图片 URL |
| det_thresh | float | 否 | 检测阈值，默认 0.5，范围 0-1 |
| max_faces | int | 否 | 最大返回人脸数，默认 10 |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "face_count": 2,
    "faces": [
      {
        "face_id": "face_001",
        "bbox": [100, 80, 200, 220],
        "landmarks": {
          "left_eye": [130, 140],
          "right_eye": [170, 140],
          "nose": [150, 170],
          "left_mouth": [130, 190],
          "right_mouth": [170, 190]
        },
        "confidence": 0.9987,
        "attributes": {
          "gender": "female",
          "gender_confidence": 0.95,
          "age": 25,
          "emotion": "happy"
        }
      }
    ],
    "image_size": [1920, 1080],
    "elapsed": 0.156
  }
}
```

#### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| face_id | string | 人脸唯一标识（本次检测） |
| bbox | array | 人脸框坐标 [x, y, width, height] |
| landmarks | object | 5 点人脸关键点 |
| confidence | float | 检测置信度 |
| attributes | object | 人脸属性（性别、年龄、表情） |

### 2. 人脸特征提取

提取人脸特征向量（Embedding）。

**POST** `/face/embedding`

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是* | 图片文件 |
| url | string | 是* | 图片 URL |
| bbox | array | 否 | 指定人脸框 [x, y, w, h] |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "embedding_id": "emb_001",
    "embedding": [0.023, -0.156, 0.089, ...],
    "dimension": 512,
    "model": "ir_se_50",
    "elapsed": 0.089
  }
}
```

### 3. 人脸比对

比较两张人脸的相似度。

**POST** `/face/compare`

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file1 | File | 是* | 第一张图片 |
| url1 | string | 是* | 第一张图片 URL |
| file2 | File | 是* | 第二张图片 |
| url2 | string | 是* | 第二张图片 URL |
| threshold | float | 否 | 匹配阈值，默认 0.6 |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "similarity": 0.8234,
    "is_match": true,
    "threshold": 0.6,
    "confidence": "high",
    "elapsed": 0.234
  }
}
```

#### 相似度说明

| 相似度范围 | 匹配结果 | 置信度 |
|-----------|----------|--------|
| 0.80 - 1.00 | 同一人 | 高 |
| 0.60 - 0.80 | 可能是同一人 | 中 |
| 0.00 - 0.60 | 不同人 | 低 |

### 4. 人脸搜索

在已注册的人脸库中搜索相似人脸。

**POST** `/face/search`

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是* | 查询图片 |
| url | string | 是* | 查询图片 URL |
| top_k | int | 否 | 返回结果数，默认 5 |
| threshold | float | 否 | 匹配阈值，默认 0.6 |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "query_face": {
      "bbox": [100, 80, 200, 220],
      "confidence": 0.998
    },
    "results": [
      {
        "person_id": "person_001",
        "person_name": "张三",
        "similarity": 0.89,
        "registered_at": "2024-01-15T08:30:00Z"
      }
    ],
    "elapsed": 0.345
  }
}
```

### 5. 注册人脸

将人脸注册到人脸库。

**POST** `/face/register`

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是* | 人脸图片 |
| person_id | string | 否 | 人员 ID（不指定则自动生成） |
| person_name | string | 是 | 人员名称 |
| metadata | object | 否 | 附加信息 |

#### 响应示例

```json
{
  "code": 201,
  "message": "注册成功",
  "data": {
    "person_id": "person_001",
    "person_name": "张三",
    "face_count": 1,
    "registered_at": "2024-01-20T10:30:00Z"
  }
}
```

## 目标检测模块

### 1. 通用目标检测

检测图片中的通用物体。

**POST** `/detection/detect`

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是* | 图片文件 |
| url | string | 是* | 图片 URL |
| conf_thresh | float | 否 | 置信度阈值，默认 0.5 |
| nms_thresh | float | 否 | NMS 阈值，默认 0.45 |
| classes | array | 否 | 指定检测类别，默认全部 |

#### 支持的类别

```
person, bicycle, car, motorcycle, airplane, bus, train, truck, boat, 
traffic light, fire hydrant, stop sign, parking meter, bench, bird, 
cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe, backpack, 
umbrella, handbag, tie, suitcase, frisbee, skis, snowboard, sports ball, 
kite, baseball bat, baseball glove, skateboard, surfboard, tennis racket, 
bottle, wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich, 
orange, broccoli, carrot, hot dog, pizza, donut, cake, chair, couch, 
potted plant, bed, dining table, toilet, tv, laptop, mouse, remote, 
keyboard, cell phone, microwave, oven, toaster, sink, refrigerator, 
book, clock, vase, scissors, teddy bear, hair drier, toothbrush
```

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "detections": [
      {
        "class_id": 0,
        "class_name": "person",
        "confidence": 0.9234,
        "bbox": [100, 150, 200, 400]
      },
      {
        "class_id": 2,
        "class_name": "car",
        "confidence": 0.8765,
        "bbox": [300, 200, 500, 350]
      }
    ],
    "detection_count": 5,
    "elapsed": 0.456
  }
}
```

### 2. 行人检测

专门检测图片中的行人。

**POST** `/detection/persons`

#### 请求参数

与 `/detection/detect` 相同，但只返回 `person` 类别。

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "person_count": 3,
    "persons": [
      {
        "bbox": [100, 150, 200, 400],
        "confidence": 0.9234,
        "pose": "standing"
      }
    ],
    "elapsed": 0.234
  }
}
```

### 3. 目标统计

统计图片中各类目标的数量。

**POST** `/detection/count`

#### 请求参数

与 `/detection/detect` 相同。

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 8,
    "by_class": {
      "person": 3,
      "car": 2,
      "bicycle": 2,
      "dog": 1
    },
    "elapsed": 0.345
  }
}
```

## 票据识别模块

### 1. 票据类型检测

自动检测票据类型。

**POST** `/tickets/detect-type`

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是* | 票据图片 |
| url | string | 是* | 图片 URL |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "ticket_type": "train_ticket",
    "confidence": 0.95,
    "possible_types": [
      {"type": "train_ticket", "confidence": 0.95},
      {"type": "invoice", "confidence": 0.03},
      {"type": "receipt", "confidence": 0.02}
    ]
  }
}
```

### 2. 火车票识别

识别火车票信息。

**POST** `/tickets/train`

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "ticket_type": "train_ticket",
    "fields": {
      "ticket_no": "G12345678",
      "train_no": "G1234",
      "departure_station": "北京南",
      "arrival_station": "上海虹桥",
      "departure_date": "2024-02-10",
      "departure_time": "08:00",
      "seat_class": "二等座",
      "seat_no": "12车 03A号",
      "price": 553.5,
      "passenger_name": "张三",
      "id_card": "110101********1234",
      "ticket_gate": "12A",
      "sale_station": "北京南站"
    },
    "confidence": 0.94,
    "elapsed": 0.678
  }
}
```

### 3. 增值税发票识别

识别增值税发票信息。

**POST** `/tickets/invoice`

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "ticket_type": "vat_invoice",
    "fields": {
      "invoice_code": "011001900211",
      "invoice_no": "12345678",
      "invoice_date": "2024-01-15",
      "buyer_name": "某某科技有限公司",
      "buyer_tax_no": "91110108MA00XXXXXX",
      "seller_name": "北京某某商贸有限公司",
      "seller_tax_no": "91110108MA00YYYYYY",
      "total_amount": 1000.00,
      "total_tax": 130.00,
      "total_with_tax": 1130.00,
      "items": [
        {
          "name": "办公用品",
          "specification": "A4纸",
          "unit": "箱",
          "quantity": 10,
          "price": 100.00,
          "amount": 1000.00,
          "tax_rate": "13%",
          "tax": 130.00
        }
      ]
    },
    "confidence": 0.96,
    "elapsed": 1.234
  }
}
```

### 4. 通用票据识别

自动识别票据类型并提取信息。

**POST** `/tickets/recognize`

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是* | 票据图片 |
| url | string | 是* | 图片 URL |
| ticket_type | string | 否 | 指定票据类型: `auto`, `train`, `invoice`, `receipt`，默认 `auto` |

#### 支持的票据类型

| 类型值 | 说明 |
|--------|------|
| train_ticket | 火车票 |
| vat_invoice | 增值税发票 |
| quota_invoice | 定额发票 |
| taxi_invoice | 出租车发票 |
| flight_itinerary | 航空行程单 |
| medical_receipt | 医疗票据 |
| receipt | 通用收据 |
| bank_slip | 银行回单 |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "ticket_type": "train_ticket",
    "confidence": 0.95,
    "fields": { ... },
    "raw_text": "原始 OCR 文本",
    "elapsed": 0.789
  }
}
```

## 系统模块

### 1. 健康检查

**GET** `/health`

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "models": {
      "ocr": "loaded",
      "face": "loaded",
      "detection": "loaded"
    },
    "device": "cuda:0",
    "gpu_info": {
      "name": "NVIDIA GeForce RTX 4090",
      "memory_total": 25769803776,
      "memory_used": 2147483648
    },
    "uptime": 86400
  }
}
```

### 2. 获取模型信息

**GET** `/models`

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "models": [
      {
        "name": "ocr",
        "type": "PaddleOCR",
        "version": "3.3.2",
        "status": "loaded",
        "loaded_at": "2024-01-20T08:00:00Z"
      },
      {
        "name": "face",
        "type": "InsightFace",
        "version": "0.7.3",
        "status": "loaded",
        "loaded_at": "2024-01-20T08:00:00Z"
      }
    ]
  }
}
```

### 3. 加载/卸载模型

**POST** `/models/{model_name}/load`
**POST** `/models/{model_name}/unload`

#### 请求参数（加载）

```json
{
  "device": "cuda",    // cuda 或 cpu
  "force": false       // 是否强制重新加载
}
```

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 415 | 不支持的文件类型 |
| 422 | 图片处理失败 |
| 500 | 模型推理错误 |
| 503 | 模型未加载 |

## 性能指标

### 平均响应时间

| 接口 | CPU 模式 | GPU 模式 |
|------|----------|----------|
| /ocr/recognize | 1.5s | 0.3s |
| /face/detect | 0.5s | 0.1s |
| /face/embedding | 0.3s | 0.05s |
| /detection/detect | 1.0s | 0.2s |
| /tickets/recognize | 2.0s | 0.5s |

*测试环境: Intel i9-13900K, NVIDIA RTX 4090, 图片尺寸 1920x1080*

## 最佳实践

1. **图片预处理**
   - 建议图片宽度不超过 1920px
   - 文件大小不超过 10MB
   - 格式推荐: JPEG, PNG

2. **错误处理**
   - 网络错误: 指数退避重试
   - 429 错误: 降低请求频率
   - 500 错误: 检查图片质量

3. **性能优化**
   - 批量处理时并发数不超过 4
   - 使用 GPU 模式获得最佳性能
   - 合理设置置信度阈值减少误检
