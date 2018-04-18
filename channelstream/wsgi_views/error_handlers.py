from pyramid.view import exception_view_config


@exception_view_config(context='marshmallow.ValidationError', renderer='json')
def marshmallow_invalid_data(context, request):
    request.response.status = 422
    return context.messages


@exception_view_config(context='itsdangerous.BadTimeSignature', renderer='json')
@exception_view_config(context='itsdangerous.BadSignature', renderer='json')
def itsdangerous_signer_error(context, request):
    request.response.status = 401
    return {'request': 'Bad Signature'}
