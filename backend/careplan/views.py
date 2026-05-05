import uuid
import openai
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

# 内存存储：用字典代替数据库
# 格式：{ "order_id": { "status": "...", "content": "...", ...患者信息 } }
orders_store = {}

@api_view(['POST'])
def create_order(request):
    data = request.data

    # 生成一个唯一 ID
    order_id = str(uuid.uuid4())[:8]

    # 先把订单存进内存，状态设为 processing
    orders_store[order_id] = {
        "id": order_id,
        "status": "processing",
        "content": None,
        # 患者信息
        "patient_first_name": data.get("patient_first_name", ""),
        "patient_last_name": data.get("patient_last_name", ""),
        "mrn": data.get("mrn", ""),
        "medication_name": data.get("medication_name", ""),
        "primary_diagnosis": data.get("primary_diagnosis", ""),
        "patient_records": data.get("patient_records", ""),
    }

    # 同步调用 LLM（用户要在这里等 10-20 秒）
    try:
        care_plan_content = call_llm(orders_store[order_id])
        orders_store[order_id]["status"] = "completed"
        orders_store[order_id]["content"] = care_plan_content
    except Exception as e:
        orders_store[order_id]["status"] = "failed"
        orders_store[order_id]["content"] = str(e)

    return Response(orders_store[order_id])


@api_view(['GET'])
def get_order(request, order_id):
    if order_id not in orders_store:
        return Response({"error": "Order not found"}, status=404)

    return Response(orders_store[order_id])


def call_llm(order):
    """调用 OpenAI 生成 care plan"""
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    prompt = f"""You are a clinical pharmacist. Generate a professional care plan for this patient.

Patient Information:
- Name: {order['patient_first_name']} {order['patient_last_name']}
- MRN: {order['mrn']}
- Primary Diagnosis: {order['primary_diagnosis']}
- Medication: {order['medication_name']}
- Patient Records: {order['patient_records']}

Generate a care plan with these sections:
1. Problem List / Drug Therapy Problems (DTPs)
2. Goals (SMART)
3. Pharmacist Interventions / Plan
4. Monitoring Plan & Lab Schedule

Be specific and clinical."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )

    return response.choices[0].message.content