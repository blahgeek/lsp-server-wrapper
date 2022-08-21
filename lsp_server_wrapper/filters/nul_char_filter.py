#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ..filter_base import FilterBase, FilterContext, FilterResult, Message


class NulCharFilter(FilterBase):

    def _do_process(self, msg: Message, ctx: FilterContext) -> FilterResult:
        if not msg.is_response() or not msg.corresponding_request:
            return True
        if msg.corresponding_request.get('method') != 'textDocument/completion':
            return True
        if 'result' not in msg.msg:
            return True

        result = msg.msg['result']
        if isinstance(result, dict):
            result = result['items']
        for item in result:
            if sort_text := item.get('sortText'):
                item['sortText'] = sort_text.replace('\x00', '-')
        return Message.create_from_json(msg.msg)
