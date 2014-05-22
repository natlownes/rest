import flask
import unicodecsv as csv

from exceptions import ValueError

from flask import Response
from flask import request
from functools import wraps
from StringIO import StringIO
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
from validators import regex
from validators import required
from validators import url

from encoding import encoder


class CsvValidationError(ValueError):

  def __init__(self, message, schema):
    self.schema = schema
    super(CsvValidationError, self).__init__(message)


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

def _check_csv_schema(schema, row, row_number):
  csv_row_schema = schema(row_number=row_number)
  if not csv_row_schema(row):
    raise CsvValidationError('CSV failed validation', csv_row_schema)
  return csv_row_schema

def csv_upload(schema, fieldnames=None):
  """
  validate each row of a CSV on upload - if a row doesn't pass validation, HTTP
  400 with a body of the validation errors out of the rest schema.
  CSV must have a header

  the generator object will be passed to the view function as the rows argument
  and will return a rest.Schema for each row.  if nothing calls the generator,
  no validation will occur
  """
  def decorator(view):
    @wraps(view)
    def view_wrapper(*args, **kwargs):
      body = request.files['file'].stream
      rows = (_check_csv_schema(schema, row, i) \
          for i, row in enumerate(csv.DictReader(body, fieldnames=fieldnames),
            start=1))
      try:
        return view(rows, *args, **kwargs)
      except CsvValidationError as exc:
        return error(exc.schema)

    return view_wrapper
  return decorator

def json_csv_upload(schema, fieldnames=None):
  """
  similar to `csv_upload`, but handle bodies like {"csv": "name,a,b\nhonk,c,d"}
  """
  def decorator(wrapped):
    @wraps(wrapped)
    @view
    def view_wrapper(*args, **kwargs):
      body = kwargs.get('data')
      if not body or not body.get('csv'):
        return error({'client': ['"csv" key cannot be empty']})

      csv_data = body.get('csv').encode('utf8')

      rows = (_check_csv_schema(schema, row, i) \
          for i, row in enumerate(csv.DictReader(StringIO(csv_data),
            fieldnames=fieldnames), start=1))
      kwargs['rows'] = rows
      try:
        return wrapped(*args, **kwargs)
      except CsvValidationError as exc:
        return error(exc.schema)

    return view_wrapper
  return decorator

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
