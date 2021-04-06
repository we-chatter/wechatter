# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   interpreter.py
 
@Time    :   2021/4/6 4:39 下午
 
@Desc    :   nlu解析器
 
"""

import json
import logging
import re
from json.decoder import JSONDecodeError
from typing import Text, Optional, Dict, Any, Union, List, Tuple

logger = logging.getLogger(__name__)

class NatureLanguageInterpreter:
    async def parse(
        self,
        text: Text,
        message_id: Optional[Text] = None,
        tracker: Optional[DialogueStateTracker] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[Text, Any]:
        raise NotImplementedError(
            "Interpreter needs to be able to parse messages into structured output."
        )

    def featurize_message(self, message: Message) -> Optional[Message]:
        pass
