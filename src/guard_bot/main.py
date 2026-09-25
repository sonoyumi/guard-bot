"""Application wiring: settings, database, bot, captcha sweeper."""

from __future__ import annotations

import asyncio
import contextlib
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from guard_bot.actions import AdminCache
from guard_bot.config import load_settings
from guard_bot.db import Database
from guard_bot.handlers import captcha_loop, router
from guard_bot.rules import FloodTracker

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    db = await Database.open(settings.database_path)

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    dp["db"] = db
    dp["admins"] = AdminCache()
    dp["flood"] = FloodTracker()

    sweeper = asyncio.create_task(captcha_loop(bot, db))
    logger.info("Guard bot started")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        sweeper.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sweeper
        await db.close()
        await bot.session.close()
