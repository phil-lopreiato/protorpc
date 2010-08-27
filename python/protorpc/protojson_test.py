#!/usr/bin/env python
#
# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Tests for protorpc.protojson."""

__author__ = 'rafek@google.com (Rafe Kaplan)'

import unittest

import test_util
from protorpc import messages
from protorpc import protojson

from django.utils import simplejson


class MyMessage(messages.Message):
  """Test message containing various types."""

  class Color(messages.Enum):

    RED = 1
    GREEN = 2
    BLUE = 3

  class Nested(messages.Message):

    nested_value = messages.StringField(1)

  a_string = messages.StringField(2)
  an_integer = messages.IntegerField(3)
  a_float = messages.FloatField(4)
  a_boolean = messages.BooleanField(5)
  an_enum = messages.EnumField(Color, 6)
  a_nested = messages.MessageField(Nested, 7)
  a_repeated = messages.IntegerField(8, repeated=True)


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):

  MODULE = protojson


# TODO(rafek): Convert this test to the compliance test in test_util.
class ProtojsonTest(test_util.TestCase,
                    test_util.ProtoConformanceTestBase):
  """Test JSON encoding and decoding."""

  PROTOLIB = protojson

  def CompareEncoded(self, expected_encoded, actual_encoded):
    """JSON encoding will be laundered to remove string differences."""
    self.assertEquals(simplejson.loads(expected_encoded),
                      simplejson.loads(actual_encoded))

  encoded_empty_message = '{}'

  encoded_partial = """{
    "double_value": 1.23,
    "int64_value": -100000000000,
    "int32_value": 1020,
    "string_value": "a string",
    "enum_value": "VAL2"
  }
  """

  encoded_full = """{
    "double_value": 1.23,
    "float_value": -2.5,
    "int64_value": -100000000000,
    "uint64_value": 102020202020,
    "int32_value": 1020,
    "bool_value": true,
    "string_value": "a string\u044f",
    "bytes_value": "YSBieXRlc//+",
    "enum_value": "VAL2"
  }
  """

  encoded_repeated = """{
    "double_value": [1.23, 2.3],
    "float_value": [-2.5, 0.5],
    "int64_value": [-100000000000, 20],
    "uint64_value": [102020202020, 10],
    "int32_value": [1020, 718],
    "bool_value": [true, false],
    "string_value": ["a string\u044f", "another string"],
    "bytes_value": ["YSBieXRlc//+", "YW5vdGhlciBieXRlcw=="],
    "enum_value": ["VAL2", "VAL1"]
  }
  """

  encoded_nested = """{
    "nested": {
      "a_value": "a string"
    }
  }
  """

  encoded_repeated_nested = """{
    "repeated_nested": [{"a_value": "a string"},
                        {"a_value": "another string"}]
  }
  """

  unexpected_tag_message = '{"unknown": "value"}'

  encoded_default_assigned = '{"a_value": "a default"}'

  encoded_nested_empty = '{"nested": {}}'

  encoded_repeated_nested_empty = '{"repeated_nested": [{}, {}]}'

  encoded_extend_message = '{"int64_value": [400, 50, 6000]}'

  def testConvertIntegerToFloat(self):
    """Test that integers passed in to float fields are converted.

    This is necessary because JSON outputs integers for numbers with 0 decimals.
    """
    message = protojson.decode_message(MyMessage, '{"a_float": 10}')

    self.assertTrue(isinstance(message.a_float, float))
    self.assertEquals(10.0, message.a_float)

  def testWrongTypeAssignment(self):
    """Test when wrong type is assigned to a field."""
    self.assertRaises(messages.ValidationError,
                      protojson.decode_message,
                      MyMessage, '{"a_string": 10}')

  def testNumericEnumeration(self):
    """Test that numbers work for enum values."""
    message = protojson.decode_message(MyMessage, '{"an_enum": 2}')

    expected_message = MyMessage()
    expected_message.an_enum = MyMessage.Color.GREEN

    self.assertEquals(expected_message, message)

  def testNullValues(self):
    """Test that null values overwrite existing values."""
    self.assertEquals(MyMessage(),
                      protojson.decode_message(MyMessage, ('{"an_integer": null,'
                                                           ' "a_nested": null,'
                                                           ' "a_repeated": null'
                                                           '}')))

  def testEmptyList(self):
    """Test that empty lists are ignored."""
    self.assertEquals(MyMessage(),
                      protojson.decode_message(MyMessage,
                                               '{"a_repeated": []}'))

  def testNotJSON(self):
    """Test error when string is not valid JSON."""
    self.assertRaises(ValueError,
                      protojson.decode_message, MyMessage, '{this is not json}')

  def testDoNotEncodeStrangeObjects(self):
    """Test trying to encode a strange object.

    The main purpose of this test is to complete coverage.  It ensures that
    the default behavior of the JSON encoder is preserved when someone tries to
    serialized an unexpected type.
    """
    class BogusObject(object):

      def check_initialized(self):
        pass

    self.assertRaises(TypeError,
                      protojson.encode_message,
                      BogusObject())

  def testMergeEmptyString(self):
    """Test merging the empty or space only string."""
    message = protojson.decode_message(test_util.OptionalMessage, '')
    self.assertEquals(test_util.OptionalMessage(), message)

    message = protojson.decode_message(test_util.OptionalMessage, ' ')
    self.assertEquals(test_util.OptionalMessage(), message)


if __name__ == '__main__':
  unittest.main()