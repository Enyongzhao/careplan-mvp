from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import services, serializers


@api_view(['POST'])
def create_order(request):
    s = serializers.CreateOrderSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    order, care_plan = services.create_order_with_careplan(s.validated_data)
    return Response({'order_id': str(order.id), 'careplan_id': care_plan.id, 'status': 'pending'}, status=202)


@api_view(['GET'])
def get_careplan_status(request, careplan_id):
    care_plan = services.get_careplan(careplan_id)
    return Response(serializers.serialize_careplan_status(care_plan))


@api_view(['GET'])
def get_order(request, order_id):
    order = services.get_order_detail(order_id)
    return Response(serializers.OrderDetailSerializer(order).data)
