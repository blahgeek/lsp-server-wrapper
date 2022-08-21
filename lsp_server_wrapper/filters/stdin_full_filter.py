#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from ..filter_base import FilterBase, FilterResult, FilterContext, Message


logger = logging.getLogger(__name__)


class StdinFullFilter(FilterBase):

    MAX_WRITER_QUEUE_SIZE = 64

    def _do_process(self, msg: Message, ctx: FilterContext) -> FilterResult:
        if (ctx.from_client and ctx.writer_queue_size > self.MAX_WRITER_QUEUE_SIZE and
            (msg.is_request() or msg.is_notification())):
            logger.warning('Dropping a message from client because server stdin queue full')
            return False
        return True

