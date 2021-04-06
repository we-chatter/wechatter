# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   model_training.py
 
@Time    :   2020/11/17 8:56 下午
 
@Desc    :   train model
 
"""

import asyncio
import os
import tempfile
from contextlib import ExitStack
from typing import (
    Text,
    NamedTuple,
    Tuple,
    Optional,
    List,
    Union,
    Dict,
)

from wechatter.shared.dm.domain import Domain

from wechatter.shared.dialogue_config import (
    DEFAULT_MODELS_PATH
)


class TrainingResult(NamedTuple):
    """Holds information about the results of training."""

    model: Optional[Text] = None
    code: int = 0


async def train_async(
domain: Union[Domain, Text],
    config: Text,
    training_files: Optional[Union[Text, List[Text]]],
    output: Text = DEFAULT_MODELS_PATH,
    dry_run: bool = False,
    force_training: bool = False,
    fixed_model_name: Optional[Text] = None,
    persist_nlu_training_data: bool = False,
    core_additional_arguments: Optional[Dict] = None,
    nlu_additional_arguments: Optional[Dict] = None,
    model_to_finetune: Optional[Text] = None,
    finetuning_epoch_fraction: float = 1.0,
) -> TrainingResult:
    """
    进行异步训练
    :param domain:
    :param config:
    :param training_files:
    :param output:
    :param dry_run:
    :param force_training: bool值，如果为True，则在数据没有变动的情况下也训练
    :param fixed_model_name: 模型名称
    :param persist_nlu_training_data:
    :param core_additional_arguments:
    :param nlu_additional_arguments:
    :param model_to_finetune:
    :param finetuning_epoch_fraction:
    :return: TrainingResult 的实例
    """
    file_importer = TrainingDataImporter.load_from_config(
        config,
        domain,
        training_files
    )
    with TempDirectoryPath(tempfile.mkdtemp()) as train_path:
        domain = await file_importer.get_domain()

        if domain.is_empty():
            nlu_model = await handle_domain_if_not_exists(
                file_importer, output, fixed_model_name
            )
            return TrainingResult(model=nlu_model)

        return await _train_async_internal(
            file_importer,
            train_path,
            output,
            dry_run,
            force_training,
            fixed_model_name,
            persist_nlu_training_data,
            core_additional_arguments=core_additional_arguments,
            nlu_additional_arguments=nlu_additional_arguments,
            model_to_finetune=model_to_finetune,
            finetuning_epoch_fraction=finetuning_epoch_fraction,
        )