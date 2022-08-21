#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import dataclasses

from .codec import Message


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class FilterContext:
    from_client: bool  # True if client -> server; False if server -> client
    writer_queue_size: int  # queue size of the writer side (server stdin, if from_client is true)


# true: accept message; false: reject message; message: new message
FilterResult = bool | Message


class FilterBase:

    def process(self, msg: Message, ctx: FilterContext) -> FilterResult:
        try:
            return self._do_process(msg, ctx)
        except Exception:
            logger.exception(f'Failed to process message by {self}')
            return True

    def _do_process(self, msg: Message, ctx: FilterContext) -> FilterResult:
        raise NotImplementedError()

    @staticmethod
    def run_filters(filters: list['FilterBase'], msg: Message, ctx: FilterContext) -> FilterResult:
        for f in filters:
            if (res := f.process(msg, ctx)) is not True:
                return res
            continue
        return True
