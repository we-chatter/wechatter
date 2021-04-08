# -*- coding: utf-8 -*-

"""
@Author  :   Xu
 
@Software:   PyCharm
 
@File    :   io.py
 
@Time    :   2021/4/2 5:23 下午
 
@Desc    :
 
"""
from collections import OrderedDict
import errno
import glob
from hashlib import md5
from io import StringIO
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Text, Type, Union, FrozenSet
import warnings
from ruamel import yaml

from wechatter.shared.exceptions import (
    FileIOException,
    FileNotFoundException,
    YamlSyntaxException
)

DEFAULT_ENCODING = 'utf-8'  # 默认用utf-8，打开文件时用


def read_file(filename: Union[Text, Path], encoding: Text = DEFAULT_ENCODING) -> Any:
    """Read text from a file."""

    try:
        with open(filename, encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundException(
            f"Failed to read file, " f"'{os.path.abspath(filename)}' does not exist."
        )
    except UnicodeDecodeError:
        raise FileIOException(
            f"Failed to read file '{os.path.abspath(filename)}', "
            f"could not read the file using {encoding} to decode "
            f"it. Please make sure the file is stored with this "
            f"encoding."
        )


def read_yaml(content: Text, reader_type: Union[Text, List[Text]] = "safe") -> Any:
    """
    Parses yaml from a text.
    解析yaml文件
    Args:
        content: A text containing yaml content.
        reader_type: Reader type to use. By default "safe" will be used
        replace_env_vars: Specifies if environment variables need to be replaced

    Raises:
        ruamel.yaml.parser.ParserError: If there was an error when parsing the YAML.
    """
    if _is_ascii(content):
        # Required to make sure emojis are correctly parsed
        content = (
            content.encode("utf-8")
                .decode("raw_unicode_escape")
                .encode("utf-16", "surrogatepass")
                .decode("utf-16")
        )

    yaml_parser = yaml.YAML(typ=reader_type)
    # yaml_parser.version = YAML_VERSION
    yaml_parser.preserve_quotes = True

    return yaml_parser.load(content) or {}


def _is_ascii(text: Text) -> bool:
    return all(ord(character) < 128 for character in text)


def write_text_file(
    content: Text,
    file_path: Union[Text, Path],
    encoding: Text = DEFAULT_ENCODING,
    append: bool = False,
) -> None:
    """
    写入文件
    Args:
        content: The content to write.
        file_path: The path to which the content should be written.
        encoding: The encoding which should be used.
        append: Whether to append to the file or to truncate the file.

    """
    mode = "a" if append else "w"
    with open(file_path, mode, encoding=encoding) as file:
        file.write(content)