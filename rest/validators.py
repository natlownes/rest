import re


def required(value):
  if value is None:
    return ['is required']

def nonempty(value):
  if not value:
    return ['cannot be empty']

def number_range(min=None, max=None):
  def test_range(value):
    if value is not None:
      if min is not None and value < min:
        return ['cannot be less than %s' % str(min)]
      if max is not None and value > max:
        return ['cannot be greater than %s' % str(max)]
  return test_range

def url(value):
  if value:
    regex = r'^http(s)?://([^/:]+\.[a-z]{2,10}|' \
      + r'([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$'
    if not re.match(regex, value):
      return ['must be a valid HTTP URL']

def multiple_choice(choices):

  def assert_choice_in_choices(value):
    if value not in choices:
      return ['Invalid selection %s' % value]

  return assert_choice_in_choices

def non_falsy_list(value):
  if not [v for v in value if v] == value:
    return ['list must contain values']
