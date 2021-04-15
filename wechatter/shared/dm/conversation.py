# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   conversation.py
 
@Time    :   2021/4/2 3:33 下午
 
@Desc    :
 
"""

from typing import Dict, List, Text, Any
from wechatter.shared.dm.events import Event


class Dialogue:
    """
    对话实例构造
    """

    def __init__(self, name: Text, events: List["Event"]) -> None:
        """
        初始化一个对话
        :param name:
        :param events:
        """
        self.name = name
        self.events = events

    def __str__(self) -> Text:
        """
        This function returns the dialogue and turns.
        """
        return "Dialogue with name '{}' and turns:\n{}".format(
            self.name, "\n\n".join([f"\t{t}" for t in self.events])
        )

    def as_dict(self) -> Dict:
        """
        This function returns the dialogue as a dictionary to assist in
        serialization.
        :return:
        """
        return {"events": [event.as_dict() for event in self.events]}

    @classmethod
    def from_parameters(cls, parameters: Dict[Text, Any]) -> "Dialogue":
        """Create `Dialogue` from parameters.

        Args:
            parameters: Serialised dialogue, should contain keys 'name' and 'events'.

        Returns:
            Deserialised `Dialogue`.

        """

        return cls(
            parameters.get("name"),
            [Event.from_parameters(evt) for evt in parameters.get("events")],
        )

