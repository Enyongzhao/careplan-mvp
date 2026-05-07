from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import CarePlan, Order
from . import services, serializers


@api_view(['POST'])
def create_order(request):
    # DEBUG ① views.py — request.data 是 DRF 解析后的 dict，不是原始 JSON 字符串
    print(f"\n[DEBUG views] request.data type={type(request.data)}")
    print(f"[DEBUG views] request.data = {dict(request.data)}")

    order, care_plan = services.create_order_with_careplan(request.data)

    # DEBUG ④ views.py — service 返回的是 Django model 实例，不是 dict
    print(f"[DEBUG views] order type={type(order)}, id={order.id}")
    print(f"[DEBUG views] care_plan type={type(care_plan)}, id={care_plan.id}, status={care_plan.status}")

    response_data = {'order_id': str(order.id), 'careplan_id': care_plan.id, 'status': 'pending'}
    print(f"[DEBUG views] response_data = {response_data}\n")
    return Response(response_data, status=202)


@api_view(['GET'])
def get_careplan_status(request, careplan_id):
    try:
        care_plan = services.get_careplan(careplan_id)
    except CarePlan.DoesNotExist:
        return Response({'error': 'CarePlan not found'}, status=404)
    return Response(serializers.serialize_careplan_status(care_plan))


@api_view(['GET'])
def get_order(request, order_id):
    try:
        order = services.get_order_detail(order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=404)
    return Response(serializers.OrderDetailSerializer(order).data)
