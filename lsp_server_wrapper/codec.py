#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json


class Message:

    corresponding_request: dict | None = None

    def __init__(self, msg_content: bytes, msg: dict):
        self.msg_content = msg_content
        self.msg = msg
        if self.msg.get('jsonrpc') != '2.0':
            raise ValueError(f'Invalid jsonrpc version in message')

    @staticmethod
    def create_from_bytes(msg_content: bytes):
        return Message(msg_content, json.loads(msg_content))

    @staticmethod
    def create_from_json(msg: dict):
        return Message(json.dumps(msg).encode(), msg)

    def is_request(self) -> bool:
        return 'method' in self.msg and 'id' in self.msg

    def is_notification(self) -> bool:
        return 'method' in self.msg and 'id' not in self.msg

    def is_response(self) -> bool:
        return ('result' in self.msg or 'error' in self.msg) and 'id' in self.msg


async def read_message(reader: asyncio.StreamReader) -> Message | None:
    content_length = 0
    while line := (await reader.readline()).strip():
        key, value = line.split(b':', 1)
        if key == b'Content-Length':
            content_length = int(value.strip())
    if content_length == 0:
        return None
    content = await reader.readexactly(content_length)
    return Message.create_from_bytes(content)


async def write_message(writer: asyncio.StreamWriter, msg: Message):
    writer.write(f'Content-Length: {len(msg.msg_content)}\r\n'.encode())
    writer.write(b'\r\n')
    writer.write(msg.msg_content)
    await writer.drain()
