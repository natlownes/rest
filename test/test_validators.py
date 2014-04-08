from unittest import TestCase

from rest.validators import required
from rest.validators import non_falsy_list


class TestValidators(TestCase):

  def test_required(self):
    self.assert_fails_validation(required(None), 'is required')
    self.assert_passes_validation(required('a little something'))

  def test_invalid_non_falsy_lists(self):
    self.assert_fails_validation(non_falsy_list(['']),
       'list must contain values')
    self.assert_fails_validation(non_falsy_list([u'', u'']),
      'list must contain values')
    self.assert_fails_validation(non_falsy_list([u'', u'bugs']),
      'list must contain values')
    self.assert_fails_validation(non_falsy_list([None]),
      'list must contain values')
    self.assert_fails_validation(non_falsy_list([False]),
      'list must contain values')

  def test_valid_non_falsy_lists(self):
    self.assert_passes_validation(non_falsy_list([u'long hots']))
    self.assert_passes_validation(non_falsy_list(['long hots']))


################################################################################
# validation assertion methods
################################################################################


  def assert_passes_validation(self, validation):
    message = 'expected validaton to pass'
    if validation:
      failed_validation_messages = ', '.join(validation)
      message = '{0}, but failed with "{1}"'.format(message,
        failed_validation_messages)

    self.assertIsNone(validation, message)

  def assert_fails_validation(self, validation, expected_message):
    message = 'expected validation to fail'
    self.assertIsNotNone(validation, message + ', but passed all checks')

    failed_validation_messages = ', '.join(validation)
    not_in_message = '{0} with "{1}", got "{2}"'.format(message,
      expected_message, failed_validation_messages)

    self.assertIn(expected_message, validation, not_in_message)
