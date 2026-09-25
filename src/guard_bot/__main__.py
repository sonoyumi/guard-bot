"""Entry points: `python -m guard_bot` or the `guard-bot` command."""

import asyncio
import contextlib

from guard_bot.main import main


def run() -> None:
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())


if __name__ == "__main__":
    run()
