#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..filter_base import FilterBase
from .stdin_full_filter import StdinFullFilter
from .nul_char_filter import NulCharFilter


def get_all_filters() -> list[FilterBase]:
    return [
        StdinFullFilter(),
        NulCharFilter(),
    ]
