# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   multi_skills.py
 
@Time    :   2021/4/9 11:10 下午
 
@Desc    :   多技能管理，技能中控

             思路是将domain - intent - slot 通过graph的形式表示出来，
             这样可以更好的判断哪些slot需要更新
 
"""

import os
import logging
from functools import reduce
from typing import Text, Set, Dict, Optional, List, Union, Any

import wechatter.shared.data
import wechatter.shared.utils.io
from wechatter.shared.dm.domain import Domain


logger = logging.getLogger(__name__)


class MultiSkillImporter(TrainingDataImporter):
    """
    多技能数据
    """
    def __init__(
        self,
        config_file: Text,
        domain_path: Optional[Text] = None,
        training_data_paths: Optional[Union[List[Text], Text]] = None,
        project_directory: Optional[Text] = None,
    ):
        self.config = wechatter.shared.utils.io.read_model_configuration(config_file)
        if domain_path:
            self._domain_paths = [domain_path]
        else:
            self._domain_paths = []
        self._story_paths = []
        self._e2e_story_paths = []
        self._nlu_paths = []
        self._imports = []
        self._additional_paths = training_data_paths or []
        self._project_directory = project_directory or os.path.dirname(config_file)

        self._init_from_dict(self.config, self._project_directory)

        extra_nlu_files = wechatter.shared.data.get_data_files(
            training_data_paths, wechatter.shared.data.is_nlu_file
        )
        extra_story_files = wechatter.shared.data.get_data_files(
            training_data_paths, wechatter.shared.data.is_story_file
        )
        self._story_paths += extra_story_files
        self._nlu_paths += extra_nlu_files

        logger.debug(
            "Selected projects: {}".format("".join([f"\n-{i}" for i in self._imports]))
        )

        mark_as_experimental_feature(feature_name="MultiProjectImporter")

    def _init_from_path(self, path: Text) -> None:
        if os.path.isfile(path):
            self._init_from_file(path)
        elif os.path.isdir(path):
            self._init_from_directory(path)

    def _init_from_file(self, path: Text) -> None:
        path = os.path.abspath(path)
        if os.path.exists(path) and rasa.shared.data.is_config_file(path):
            config = rasa.shared.utils.io.read_config_file(path)

            parent_directory = os.path.dirname(path)
            self._init_from_dict(config, parent_directory)
        else:
            rasa.shared.utils.io.raise_warning(
                f"'{path}' does not exist or is not a valid config file."
            )

    def _init_from_dict(self, _dict: Dict[Text, Any], parent_directory: Text) -> None:
        imports = _dict.get("imports") or []
        imports = [os.path.join(parent_directory, i) for i in imports]
        # clean out relative paths
        imports = [os.path.abspath(i) for i in imports]

        # remove duplication
        import_candidates = []
        for i in imports:
            if i not in import_candidates and not self._is_explicitly_imported(i):
                import_candidates.append(i)

        self._imports.extend(import_candidates)

        # import config files from paths which have not been processed so far
        for p in import_candidates:
            self._init_from_path(p)

    def _is_explicitly_imported(self, path: Text) -> bool:
        return not self.no_skills_selected() and self.is_imported(path)

    def _init_from_directory(self, path: Text):
        for parent, _, files in os.walk(path, followlinks=True):
            for file in files:
                full_path = os.path.join(parent, file)
                if not self.is_imported(full_path):
                    # Check next file
                    continue

                if rasa.shared.data.is_test_stories_file(full_path):
                    self._e2e_story_paths.append(full_path)
                elif Domain.is_domain_file(full_path):
                    self._domain_paths.append(full_path)
                elif rasa.shared.data.is_nlu_file(full_path):
                    self._nlu_paths.append(full_path)
                elif rasa.shared.data.is_story_file(full_path):
                    self._story_paths.append(full_path)
                elif rasa.shared.data.is_config_file(full_path):
                    self._init_from_file(full_path)

    def no_skills_selected(self) -> bool:
        return not self._imports

    def training_paths(self) -> Set[Text]:
        """Returns the paths which should be searched for training data."""

        # only include extra paths if they are not part of the current project directory
        training_paths = {
            i
            for i in self._imports
            if not self._project_directory or self._project_directory not in i
        }

        if self._project_directory:
            training_paths.add(self._project_directory)

        return training_paths

    def is_imported(self, path: Text) -> bool:
        """
        Checks whether a path is imported by a skill.
        Args:
            path: File or directory path which should be checked.

        Returns:
            `True` if path is imported by a skill, `False` if not.
        """
        absolute_path = os.path.abspath(path)

        return (
            self.no_skills_selected()
            or self._is_in_project_directory(absolute_path)
            or self._is_in_additional_paths(absolute_path)
            or self._is_in_imported_paths(absolute_path)
        )

    def _is_in_project_directory(self, path: Text) -> bool:
        if os.path.isfile(path):
            parent_directory = os.path.abspath(os.path.dirname(path))

            return parent_directory == self._project_directory
        else:
            return path == self._project_directory

    def _is_in_additional_paths(self, path: Text) -> bool:
        included = path in self._additional_paths

        if not included and os.path.isfile(path):
            parent_directory = os.path.abspath(os.path.dirname(path))
            included = parent_directory in self._additional_paths

        return included

    def _is_in_imported_paths(self, path) -> bool:
        return any(
            [rasa.shared.utils.io.is_subdirectory(path, i) for i in self._imports]
        )

    def add_import(self, path: Text) -> None:
        self._imports.append(path)

    async def get_domain(self) -> Domain:
        """Retrieves model domain (see parent class for full docstring)."""
        domains = [Domain.load(path) for path in self._domain_paths]
        return reduce(
            lambda merged, other: merged.merge(other), domains, Domain.empty()
        )

    async def get_stories(
        self,
        template_variables: Optional[Dict] = None,
        use_e2e: bool = False,
        exclusion_percentage: Optional[int] = None,
    ) -> StoryGraph:
        """Retrieves training stories / rules (see parent class for full docstring)."""
        return await utils.story_graph_from_paths(
            self._story_paths,
            await self.get_domain(),
            template_variables,
            use_e2e,
            exclusion_percentage,
        )

    async def get_conversation_tests(self) -> StoryGraph:
        """Retrieves conversation test stories (see parent class for full docstring)."""
        return await utils.story_graph_from_paths(
            self._e2e_story_paths, await self.get_domain(), use_e2e=True,
        )

    async def get_config(self) -> Dict:
        """Retrieves model config (see parent class for full docstring)."""
        return self.config

    async def get_nlu_data(self, language: Optional[Text] = "en") -> TrainingData:
        """Retrieves NLU training data (see parent class for full docstring)."""
        return utils.training_data_from_paths(self._nlu_paths, language)


class MultiSkillGraphReprezentation:
    """
    将domain - intent - slot 通过graph的形式表示出来
    """
    pass