from django.core.exceptions import ObjectDoesNotExist
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class BaseAppException(Exception):
    http_status: int = 500
    type: str = 'server_error'

    def __init__(self, message: str, code: str, detail: dict = None):
        self.message = message
        self.code = code
        self.detail = detail or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'code': self.code,
            'message': self.message,
            'detail': self.detail,
        }


class ValidationError(BaseAppException):
    http_status = 400
    type = 'validation_error'


class BlockError(BaseAppException):
    http_status = 409
    type = 'block_error'


class WarningException(BaseAppException):
    http_status = 200
    type = 'warning'


def app_exception_handler(exc, context):
    # ① 我们自己的异常
    if isinstance(exc, BaseAppException):
        return Response(exc.to_dict(), status=exc.http_status)

    # ② Django ORM DoesNotExist → 404
    if isinstance(exc, ObjectDoesNotExist):
        return Response({
            'type': 'not_found',
            'code': 'not_found',
            'message': 'The requested resource was not found.',
            'detail': {},
        }, status=404)

    # ③ DRF serializer 校验失败
    if isinstance(exc, drf_exceptions.ValidationError):
        return Response({
            'type': 'validation_error',
            'code': 'validation_error',
            'message': 'Validation failed.',
            'detail': exc.detail,
        }, status=400)

    # ④ 其他（认证、权限等）交给 DRF 默认处理
    return drf_exception_handler(exc, context)
