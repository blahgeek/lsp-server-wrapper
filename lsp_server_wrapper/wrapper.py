#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import typing as tp
import contextlib

from .codec import read_message, write_message, Message
from .async_stdio import create_async_stdio
from .filter_base import FilterContext, FilterBase
from .filters import get_all_filters


logger = logging.getLogger(__name__)

MessageQueue = asyncio.Queue[Message | None]


def _make_reject_response(msg: Message) -> Message | None:
    if not msg.is_request():
        return None
    response = {
        'jsonrpc': '2.0',
        'id': msg.msg['id'],
        'error': {
            'code': -32803,  # RequestFailed
            'message': 'Request rejected by lsp-server-wrapper',
        },
    }
    return Message.create_from_json(response)


class Wrapper:

    def __init__(self, cmd: list[str]):
        self._cmd = cmd
        self._input_queue = MessageQueue()
        self._output_queue = MessageQueue()
        self._filters = get_all_filters()
        # (from_client, request_id) -> message body
        self._pending_requests: dict[tuple[bool, tp.Any], dict] = {}

    async def start(self):
        logger.info(f'Starting lsp server {self._cmd} ...')
        self._proc = await asyncio.create_subprocess_exec(
            *self._cmd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
        self._proc_stdin = tp.cast(asyncio.StreamWriter, self._proc.stdin)
        self._proc_stdout = tp.cast(asyncio.StreamReader, self._proc.stdout)

        self._stdin, self._stdout = await create_async_stdio()

    async def _run_write(self, queue: MessageQueue, writer: asyncio.StreamWriter):
        while msg := await queue.get():
            await write_message(writer, msg)
        logger.info(f'Finished writing to {writer}')

    async def _run_read(self,
                        reader: asyncio.StreamReader,
                        queue: MessageQueue,
                        response_queue: MessageQueue,
                        from_client: bool):
        while msg := await read_message(reader):
            # try to fill corresponding request
            if msg.is_response():
                pending_request_key = (not from_client, msg.msg['id'])
                if request := self._pending_requests.get(pending_request_key):
                    msg.corresponding_request = request
                    del self._pending_requests[pending_request_key]

            filter_ctx = FilterContext(from_client=from_client, writer_queue_size=queue.qsize())
            filter_res = FilterBase.run_filters(self._filters, msg, filter_ctx)
            match filter_res:
                case True:
                    pass
                case False:
                    if reject_msg := _make_reject_response(msg):
                        await response_queue.put(reject_msg)
                    continue
                case Message():
                    msg = filter_res

            if msg.is_request():
                self._pending_requests[(from_client, msg.msg['id'])] = msg.msg
            await queue.put(msg)

        logger.info(f'Got EOF from {reader} (from client? {from_client}), stop reading')
        await queue.put(None)

    async def run(self):
        await asyncio.wait([
            self._run_write(self._input_queue, self._proc_stdin),
            self._run_write(self._output_queue, self._stdout),
            self._run_read(self._proc_stdout, self._output_queue, self._input_queue, False),
            self._run_read(self._stdin, self._input_queue, self._output_queue, True),
        ], return_when=asyncio.FIRST_COMPLETED)

    async def terminate(self):
        with contextlib.suppress(ProcessLookupError):
            self._proc.terminate()
        await self._proc.communicate()

