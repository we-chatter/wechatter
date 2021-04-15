# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   tracker_store.py
 
@Time    :   2021/4/1 3:32 下午
 
@Desc    :   对话状态存储
 
"""

import contextlib
import itertools
import json
import logging
import os
import pickle
from datetime import datetime, timezone

from time import sleep
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Text,
    Union,
    TYPE_CHECKING,
)
from wechatter.shared.dm.conversation import Dialogue
from wechatter.shared.dm.domain import Domain
from wechatter.shared.dm.events import SessionStarted
from wechatter.shared.exceptions import ConnectionException

from wechatter.utils.endpoints import EndpointConfig

logger = logging.getLogger(__name__)


class TrackerStore:
    """
    Represents common behavior and interface for all `TrackerStore`s.
    """

    def __init__(
            self,
            domain: Optional[Domain],
            event_broker: Optional[EventBroker] = None,
            **kwargs: Dict[Text, Any],
    ) -> None:
        """Create a TrackerStore.

        Args:
            domain: The `Domain` to initialize the `DialogueStateTracker`.
            event_broker: An event broker to publish any new events to another
                destination.
            kwargs: Additional kwargs.
        """
        self.domain = domain
        self.event_broker = event_broker
        self.max_event_history = None

        # TODO: Remove this in Rasa Open Source 3.0
        self.retrieve_events_from_previous_conversation_sessions: Optional[bool] = None
        self._set_deprecated_kwargs_and_emit_warning(kwargs)

    def _set_deprecated_kwargs_and_emit_warning(self, kwargs: Dict[Text, Any]) -> None:
        retrieve_events_from_previous_conversation_sessions = kwargs.get(
            "retrieve_events_from_previous_conversation_sessions"
        )

        if retrieve_events_from_previous_conversation_sessions is not None:
            rasa.shared.utils.io.raise_deprecation_warning(
                f"Specifying the `retrieve_events_from_previous_conversation_sessions` "
                f"kwarg for the `{self.__class__.__name__}` class is deprecated and "
                f"will be removed in Rasa Open Source 3.0. "
                f"Please use the `retrieve_full_tracker()` method instead."
            )
            self.retrieve_events_from_previous_conversation_sessions = (
                retrieve_events_from_previous_conversation_sessions
            )

    @staticmethod
    def create(
            obj: Union["TrackerStore", EndpointConfig, None],
            domain: Optional[Domain] = None,
            event_broker: Optional[EventBroker] = None,
    ) -> "TrackerStore":
        """Factory to create a tracker store."""
        if isinstance(obj, TrackerStore):
            return obj

        from botocore.exceptions import BotoCoreError
        import pymongo.errors
        import sqlalchemy.exc

        try:
            return _create_from_endpoint_config(obj, domain, event_broker)
        except (
                BotoCoreError,
                pymongo.errors.ConnectionFailure,
                sqlalchemy.exc.OperationalError,
        ) as error:
            raise ConnectionException("Cannot connect to tracker store.") from error

    def get_or_create_tracker(
            self,
            sender_id: Text,
            max_event_history: Optional[int] = None,
            append_action_listen: bool = True,
    ) -> "DialogueStateTracker":
        """Returns tracker or creates one if the retrieval returns None.

        Args:
            sender_id: Conversation ID associated with the requested tracker.
            max_event_history: Value to update the tracker store's max event history to.
            append_action_listen: Whether or not to append an initial `action_listen`.
        """
        self.max_event_history = max_event_history

        tracker = self.retrieve(sender_id)

        if tracker is None:
            tracker = self.create_tracker(
                sender_id, append_action_listen=append_action_listen
            )

        return tracker

    def init_tracker(self, sender_id: Text) -> "DialogueStateTracker":
        """Returns a Dialogue State Tracker"""
        return DialogueStateTracker(
            sender_id,
            self.domain.slots if self.domain else None,
            max_event_history=self.max_event_history,
        )

    def create_tracker(
            self, sender_id: Text, append_action_listen: bool = True
    ) -> DialogueStateTracker:
        """Creates a new tracker for `sender_id`.

        The tracker begins with a `SessionStarted` event and is initially listening.

        Args:
            sender_id: Conversation ID associated with the tracker.
            append_action_listen: Whether or not to append an initial `action_listen`.

        Returns:
            The newly created tracker for `sender_id`.
        """
        tracker = self.init_tracker(sender_id)

        if append_action_listen:
            tracker.update(ActionExecuted(ACTION_LISTEN_NAME))

        self.save(tracker)

        return tracker

    def save(self, tracker: DialogueStateTracker) -> None:
        """Save method that will be overridden by specific tracker."""
        raise NotImplementedError()

    def exists(self, conversation_id: Text) -> bool:
        """Checks if tracker exists for the specified ID.

        This method may be overridden by the specific tracker store for
        faster implementations.

        Args:
            conversation_id: Conversation ID to check if the tracker exists.

        Returns:
            `True` if the tracker exists, `False` otherwise.
        """
        return self.retrieve(conversation_id) is not None

    def retrieve(self, sender_id: Text) -> Optional[DialogueStateTracker]:
        """Retrieves tracker for the latest conversation session.

        This method will be overridden by the specific tracker store.

        Args:
            sender_id: Conversation ID to fetch the tracker for.

        Returns:
            Tracker containing events from the latest conversation sessions.
        """
        raise NotImplementedError()

    def retrieve_full_tracker(
            self, conversation_id: Text
    ) -> Optional[DialogueStateTracker]:
        """Retrieve method for fetching all tracker events across conversation sessions
        that may be overridden by specific tracker.

        The default implementation uses `self.retrieve()`.

        Args:
            conversation_id: The conversation ID to retrieve the tracker for.

        Returns:
            The fetch tracker containing all events across session starts.
        """
        return self.retrieve(conversation_id)

    def stream_events(self, tracker: DialogueStateTracker) -> None:
        """Streams events to a message broker"""
        offset = self.number_of_existing_events(tracker.sender_id)
        events = tracker.events
        for event in list(itertools.islice(events, offset, len(events))):
            body = {"sender_id": tracker.sender_id}
            body.update(event.as_dict())
            self.event_broker.publish(body)

    def number_of_existing_events(self, sender_id: Text) -> int:
        """Return number of stored events for a given sender id."""
        old_tracker = self.retrieve(sender_id)

        return len(old_tracker.events) if old_tracker else 0

    def keys(self) -> Iterable[Text]:
        """Returns the set of values for the tracker store's primary key"""
        raise NotImplementedError()

    @staticmethod
    def serialise_tracker(tracker: DialogueStateTracker) -> Text:
        """Serializes the tracker, returns representation of the tracker."""
        dialogue = tracker.as_dialogue()

        return json.dumps(dialogue.as_dict())

    @staticmethod
    def _deserialize_dialogue_from_pickle(
            sender_id: Text, serialised_tracker: bytes
    ) -> Dialogue:
        # TODO: Remove in Rasa Open Source 3.0
        rasa.shared.utils.io.raise_deprecation_warning(
            f"Found pickled tracker for "
            f"conversation ID '{sender_id}'. Deserialization of pickled "
            f"trackers is deprecated and will be removed in Rasa Open Source 3.0. Rasa "
            f"will perform any future save operations of this tracker using json "
            f"serialisation."
        )

        return pickle.loads(serialised_tracker)

    def deserialise_tracker(
            self, sender_id: Text, serialised_tracker: Union[Text, bytes]
    ) -> Optional[DialogueStateTracker]:
        """Deserializes the tracker and returns it."""

        tracker = self.init_tracker(sender_id)

        try:
            dialogue = Dialogue.from_parameters(json.loads(serialised_tracker))
        except UnicodeDecodeError:
            dialogue = self._deserialize_dialogue_from_pickle(
                sender_id, serialised_tracker
            )

        tracker.recreate_from_dialogue(dialogue)

        return tracker
