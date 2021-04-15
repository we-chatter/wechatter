# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   exceptions.py
 
@Time    :   2021/4/15 3:54 下午
 
@Desc    :   异常处理
 
"""

from typing import Text

from wechatter.shared.exceptions import WechatterException

class ModelNotFound(WechatterException):
    """Raised when a model is not found in the path provided by the user."""


class NoEventsToMigrateError(WechatterException):
    """Raised when no events to be migrated are found."""


class NoConversationsInTrackerStoreError(WechatterException):
    """Raised when a tracker store does not contain any conversations."""


class NoEventsInTimeRangeError(WechatterException):
    """Raised when a tracker store does not contain events within a given time range."""


class MissingDependencyException(WechatterException):
    """Raised if a python package dependency is needed, but not installed."""


class PublishingError(WechatterException):
    """Raised when publishing of an event fails.

    Attributes:
        timestamp -- Unix timestamp of the event during which publishing fails.
    """

    def __init__(self, timestamp: float) -> None:
        self.timestamp = timestamp
        super(PublishingError, self).__init__()

    def __str__(self) -> Text:
        """Returns string representation of exception."""
        return str(self.timestamp)