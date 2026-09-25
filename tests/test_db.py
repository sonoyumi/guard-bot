import pytest

from guard_bot.db import Captcha, Database
from guard_bot.rules import ChatSettings


@pytest.fixture
async def db():
    database = await Database.open(":memory:")
    yield database
    await database.close()


async def test_settings_default_and_saved(db):
    assert await db.get_settings(1) == ChatSettings()
    custom = ChatSettings(block_links=False, stopwords=frozenset({"спам"}))
    await db.save_settings(1, custom)
    await db.save_settings(1, custom.updated(warn_limit=7))  # upsert
    assert await db.get_settings(1) == custom.updated(warn_limit=7)
    assert await db.get_settings(2) == ChatSettings()  # chats are independent


async def test_warnings_count_per_chat_and_reset(db):
    assert [await db.add_warning(1, 7) for _ in range(3)] == [1, 2, 3]
    assert await db.add_warning(2, 7) == 1
    await db.reset_warnings(1, 7)
    assert await db.add_warning(1, 7) == 1


async def test_captcha_lifecycle(db):
    await db.add_captcha(Captcha(1, 7, 100, expires_at=50))
    await db.add_captcha(Captcha(1, 8, 101, expires_at=500))
    assert await db.has_captcha(1, 7)
    assert [c.user_id for c in await db.expired_captchas(now=60)] == [7]
    popped = await db.pop_captcha(1, 7)
    assert popped == Captcha(1, 7, 100, 50)
    assert not await db.has_captcha(1, 7)
    assert await db.pop_captcha(1, 7) is None


async def test_action_log_newest_first(db):
    await db.log(1, 7, "Ann", "warn", "ссылка")
    await db.log(1, 7, "Ann", "mute", "ссылка")
    await db.log(2, 8, "Bob", "warn", "флуд")
    actions = await db.recent_actions(1)
    assert [a.action for a in actions] == ["mute", "warn"]
