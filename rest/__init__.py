import flask

from flask import Response
from functools import wraps
from werkzeug.wrappers import BaseResponse

from schema import Schema

from model import Model

from fields import Bool
from fields import DateTime
from fields import Dict
from fields import Dollars
from fields import Float
from fields import Int
from fields import List
from fields import NoneString
from fields import ReadOnly
from fields import String
from fields import StringBool
from fields import TruthyOnlyList
from fields import URL
from fields import WriteOnce
from fields import WriteOnly

from validators import multiple_choice
from validators import nonempty
from validators import number_range
from validators import required
from validators import url

from encoding import encoder


def view(func):
  @wraps(func)
  def wrapped(*args, **kwargs):
    request = flask.request
    codec   = encoder(request)
    if request.method in ['POST', 'PUT']:
      # check for multipart form data. this will be submitted with the jquery
      # forms plugin, which makes the request slightly different from
      # the backbone request.
      #
      # right now, since we're only accepting CSV files as upload this way,
      # we don't need to save the file anywhere, but we'll simply add the files
      # to the data hash keyed with the name values.
      if 'CONTENT_TYPE' in request.environ \
          and ('multipart/form-data' in request.environ['CONTENT_TYPE']
            or 'application/x-www-form-urlencoded' \
              in request.environ['CONTENT_TYPE']):
        data = request.form.copy()
        data.update(request.files)
        kwargs['data'] = data
      else:
        try:
          kwargs['data'] = codec.decode(request)
        except Exception, e:
          return error({
            'client': [str(e)]
          })

    return _serialize(func(*args, **kwargs))
  return wrapped

def error(msg):
  codec = encoder(flask.request, 'errors')
  response = Response(status=400)

  if isinstance(msg, dict):
    response.data = codec.encode(msg)
  else:
    response.data = codec.encode(msg._errors)
  return response

def created(schema):
  response = Response(status=201)
  response.data = _serialize(schema)
  return response

def deleted(schema=None):
  return Response(status=204)

def _serialize(item, request=None):
  if request is None:
    request = flask.request
  codec = encoder(request)

  if isinstance(item, BaseResponse):
    return item

  if hasattr(item, '__iter__') and not isinstance(item, dict):
    return codec.encode([_simplify(i) for i in item])

  return codec.encode(_simplify(item))

def _simplify(item):
  if hasattr(item, '_get'):
    return item._get()
  return item
