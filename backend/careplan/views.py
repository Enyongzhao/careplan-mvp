from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import services, serializers
from .adapters import get_adapter


@api_view(['POST'])
def create_order(request):
    source = request.data.get('source', 'web_form')
    adapter = get_adapter(source)  # BlockError 自动往上冒，handler 接住

    if source == 'web_form':
        s = serializers.CreateOrderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        internal_order = adapter.parse(s.validated_data).transform()
    else:
        internal_order = adapter.ingest(request.data)

    order, care_plan = services.create_order_with_careplan(internal_order.to_dict())
    return Response({'order_id': str(order.id), 'careplan_id': care_plan.id, 'status': 'pending'}, status=202)


@api_view(['GET'])
def get_careplan_status(request, careplan_id):
    care_plan = services.get_careplan(careplan_id)
    return Response(serializers.serialize_careplan_status(care_plan))


@api_view(['GET'])
def get_order(request, order_id):
    order = services.get_order_detail(order_id)
    return Response(serializers.OrderDetailSerializer(order).data)
