# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   exceptions.py
 
@Time    :   2021/4/1 5:45 下午
 
@Desc    :   异常处理
 
"""

import json
from typing import Optional, Text

import jsonschema


class WechatterException(Exception):
    """Base exception class for all errors raised by Rasa Open Source.

    These exceptions results from invalid use cases and will be reported
    to the users, but will be ignored in telemetry.
    """


class RasaCoreException(WechatterException):
    """Basic exception for errors raised by Rasa Core."""


class RasaXTermsError(WechatterException):
    """Error in case the user didn't accept the Rasa X terms."""


class InvalidParameterException(WechatterException, ValueError):
    """Raised when an invalid parameter is used."""


class MarkdownException(WechatterException, ValueError):
    """Raised if there is an error reading Markdown."""


class YamlException(WechatterException):
    """Raised if there is an error reading yaml."""

    def __init__(self, filename: Optional[Text] = None) -> None:
        """Create exception.

        Args:
            filename: optional file the error occurred in"""
        self.filename = filename


class YamlSyntaxException(YamlException):
    """Raised when a YAML file can not be parsed properly due to a syntax error."""

    def __init__(
            self,
            filename: Optional[Text] = None,
            underlying_yaml_exception: Optional[Exception] = None,
    ) -> None:
        super(YamlSyntaxException, self).__init__(filename)

        self.underlying_yaml_exception = underlying_yaml_exception

    def __str__(self) -> Text:
        if self.filename:
            exception_text = f"Failed to read '{self.filename}'."
        else:
            exception_text = "Failed to read YAML."

        if self.underlying_yaml_exception:
            self.underlying_yaml_exception.warn = None
            self.underlying_yaml_exception.note = None
            exception_text += f" {self.underlying_yaml_exception}"

        if self.filename:
            exception_text = exception_text.replace(
                'in "<unicode string>"', f'in "{self.filename}"'
            )

        exception_text += (
            "\n\nYou can use https://yamlchecker.com/ to validate the "
            "YAML syntax of your file."
        )
        return exception_text


class FileNotFoundException(WechatterException, FileNotFoundError):
    """Raised when a file, expected to exist, doesn't exist."""


class FileIOException(WechatterException):
    """Raised if there is an error while doing file IO."""


class InvalidConfigException(ValueError, WechatterException):
    """Raised if an invalid configuration is encountered."""


class UnsupportedFeatureException(RasaCoreException):
    """Raised if a requested feature is not supported."""


class SchemaValidationError(WechatterException, jsonschema.ValidationError):
    """Raised if schema validation via `jsonschema` failed."""


class InvalidEntityFormatException(WechatterException, json.JSONDecodeError):
    """Raised if the format of an entity is invalid."""

    @classmethod
    def create_from(
            cls, other: json.JSONDecodeError, msg: Text
    ) -> "InvalidEntityFormatException":
        """Creates `InvalidEntityFormatException` from `JSONDecodeError`."""
        return cls(msg, other.doc, other.pos)


class ConnectionException(WechatterException):
    """Raised when a connection to a 3rd party service fails.

    It's used by our broker and tracker store classes, when
    they can't connect to services like postgres, dynamoDB, mongo.
    """
