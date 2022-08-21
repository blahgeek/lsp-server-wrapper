#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import argparse
import asyncio

from lsp_server_wrapper.wrapper import Wrapper


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    wrapper = Wrapper(args.cmd)
    await wrapper.start()
    await wrapper.run()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

