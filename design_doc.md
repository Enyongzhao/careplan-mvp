# Software Design Document

## 1. Overview
本系统用于为 specialty pharmacy 自动生成 patient care plan。当前流程中，pharmacist 需要手动查看患者的 medical history 并撰写 care plan，每位患者耗时约 20–40 分钟，且由于人手不足导致任务严重积压。

本系统通过结构化采集 patient clinical 信息，并调用 LLM 自动生成 care plan，从而：
- 显著减少人工时间成本
- 提高生成效率与一致性
- 满足 Medicare 与 pharma 的合规与报销要求

系统同时提供数据校验、重复检测、报告导出等功能，确保数据质量与业务流程稳定。

## 2. Users & Use Cases

### Users
- 医疗工作者（medical assistant / pharmacist）
- 患者不直接使用该系统

### Use Cases

#### 创建订单并生成 Care Plan
1. 输入 patient 信息  
2. 系统 validation  
3. 重复检测  
4. WARNING 可继续 / ERROR 阻止  
5. 调用 LLM  
6. 下载 care plan  

#### 查询订单
- 按 MRN 查询历史记录

#### 导出报告
- 导出 pharma report

## 3. Tech Stack

- Frontend: Python + Django + Django REST Framework
- Backend: Node.js + Express  
- Database: PostgreSQL  
- LLM: OpenAI API  
- Testing: pytest

## 4. System Architecture

Frontend → Backend → Validation → DB → LLM → DB → Frontend

## 5. Data Model

### Patient

| 字段 | 类型 |
|------|------|
| id | UUID |
| first_name | string |
| last_name | string |
| mrn | string |
| dob | date |

### Provider

| 字段 | 类型 |
|------|------|
| id | UUID |
| name | string |
| npi | string |

### Order

| 字段 | 类型 |
|------|------|
| id | UUID |
| patient_id | UUID |
| provider_id | UUID |
| medication_name | string |

### CarePlan

| 字段 | 类型 |
|------|------|
| id | UUID |
| order_id | UUID |
| content | text |
| status | string |

## 6. API Design

POST /orders

Request Body:
~~~json
{
  "patient": {},
  "provider": {},
  "order": {}
}
~~~

Response:
{
  "status": "success | warning | error",
  "messages": [],
  "carePlan": "text content"
}

GET /orders
Query Params:

mrn
date range
medication_name

Response:
{
  "orders": [
    {
      "order": { ... },
      "carePlan": { ... }
    }
  ]
}

## 7. Business Rules

| 场景 | 处理 |
|------|------|
| 同一患者+同一药物+同一天 | ERROR |
| 同一患者+同一药物+不同天 | WARNING |
| MRN 相同 + 名字或DOB不同 | WARNING |
| 名字+DOB相同 + MRN不同 | WARNING |
| NPI 相同 + Provider名字不同 | ERROR |

## 8. Testing Strategy

包含 unit test 和 integration test
