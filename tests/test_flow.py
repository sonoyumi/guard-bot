"""End-to-end scenarios through the real aiogram Dispatcher; Telegram is replaced by a recorder."""

import time
from datetime import UTC, datetime
from itertools import count

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.methods import (
    AnswerCallbackQuery,
    BanChatMember,
    DeleteMessage,
    GetChatMember,
    RestrictChatMember,
    SendMessage,
    UnbanChatMember,
)
from aiogram.types import (
    CallbackQuery,
    Chat,
    ChatMemberMember,
    ChatMemberOwner,
    Message,
    MessageEntity,
    MessageOriginUser,
    Update,
    User,
)

from guard_bot.actions import AdminCache
from guard_bot.db import Database
from guard_bot.handlers import CaptchaCb, router, sweep_captchas
from guard_bot.rules import FloodTracker

GROUP = Chat(id=-100500, type="supergroup", title="Test group")
ADMIN = User(id=1, is_bot=False, first_name="Admin")
ANN = User(id=7, is_bot=False, first_name="Ann")
BOB = User(id=8, is_bot=False, first_name="Bob")


class TelegramRecorder(BaseSession):
    """Records Bot API calls and returns plausible results for the ones handlers read."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list = []
        self._ids = count(1000)

    async def make_request(self, bot, method, timeout=None):  # noqa: ASYNC109 - signature set by aiogram
        self.calls.append(method)
        if isinstance(method, SendMessage):
            return Message(message_id=next(self._ids), date=datetime.now(UTC), chat=GROUP, text=method.text)
        if isinstance(method, GetChatMember):
            user = User(id=method.user_id, is_bot=False, first_name="U")
            if method.user_id == ADMIN.id:
                return ChatMemberOwner(user=user, is_anonymous=False)
            return ChatMemberMember(user=user)
        return True

    async def stream_content(self, *args, **kwargs):  # pragma: no cover - not used
        raise NotImplementedError

    async def close(self) -> None:
        pass

    def of(self, kind):
        return [c for c in self.calls if isinstance(c, kind)]

    def texts(self):
        return [c.text for c in self.of(SendMessage)]


@pytest.fixture
async def env():
    session = TelegramRecorder()
    bot = Bot("42:TEST", session=session)
    db = await Database.open(":memory:")
    dp = Dispatcher()
    dp.include_router(router)
    dp["db"] = db
    dp["admins"] = AdminCache()
    dp["flood"] = FloodTracker()
    yield bot, dp, db, session
    await db.close()
    router._parent_router = None  # the module-level router can be attached to a new Dispatcher next test


_update_ids = count(1)


def message(user: User, text: str = "", **kwargs) -> Message:
    return Message(
        message_id=next(_update_ids), date=datetime.now(UTC), chat=GROUP, from_user=user, text=text, **kwargs
    )


async def feed(bot, dp, msg: Message):
    await dp.feed_update(bot, Update(update_id=next(_update_ids), message=msg))


async def press(bot, dp, user: User, data: str):
    query = CallbackQuery(id="q", from_user=user, chat_instance="ci", data=data, message=message(ADMIN, "captcha"))
    await dp.feed_update(bot, Update(update_id=next(_update_ids), callback_query=query))


async def test_captcha_passed(env):
    bot, dp, db, tg = env
    join = message(ANN, new_chat_members=[ANN], text=None)
    await feed(bot, dp, join)

    restrict = tg.of(RestrictChatMember)[-1]
    assert restrict.user_id == ANN.id and restrict.permissions.can_send_messages is False
    assert "Нажмите кнопку" in tg.texts()[-1]
    assert any(d.message_id == join.message_id for d in tg.of(DeleteMessage))  # "Ann joined" hidden
    assert await db.has_captcha(GROUP.id, ANN.id)

    await press(bot, dp, BOB, CaptchaCb(user_id=ANN.id).pack())  # someone else's button
    assert tg.of(AnswerCallbackQuery)[-1].show_alert
    assert await db.has_captcha(GROUP.id, ANN.id)

    await press(bot, dp, ANN, CaptchaCb(user_id=ANN.id).pack())
    assert tg.of(RestrictChatMember)[-1].permissions.can_send_messages is True
    assert not await db.has_captcha(GROUP.id, ANN.id)


async def test_unsolved_captcha_kicks_and_blocks_messages(env):
    bot, dp, db, tg = env
    await feed(bot, dp, message(ANN, new_chat_members=[ANN], text=None))

    spam = message(ANN, "hello")
    await feed(bot, dp, spam)  # still unverified: message removed silently
    assert tg.of(DeleteMessage)[-1].message_id == spam.message_id

    assert await sweep_captchas(bot, db, now=time.time() + 3600) == 1
    assert tg.of(BanChatMember)[-1].user_id == ANN.id
    assert tg.of(UnbanChatMember)[-1].only_if_banned is True  # kick, not a permanent ban
    assert not await db.has_captcha(GROUP.id, ANN.id)


async def test_link_warnings_then_mute(env):
    bot, dp, db, tg = env
    for i in range(1, 4):
        await feed(bot, dp, message(BOB, f"buy now https://spam.example/{i}"))
    texts = tg.texts()
    assert "Предупреждение 1/3" in texts[0] and "Предупреждение 2/3" in texts[1]
    assert "в муте на 60 мин" in texts[2]
    mute = tg.of(RestrictChatMember)[-1]
    assert mute.user_id == BOB.id and mute.until_date is not None
    assert len(tg.of(DeleteMessage)) == 3
    assert [a.action for a in await db.recent_actions(GROUP.id)] == ["mute", "warn", "warn"]


async def test_text_link_entity_and_forward(env):
    bot, dp, db, tg = env
    hidden = message(BOB, "click", entities=[MessageEntity(type="text_link", offset=0, length=5, url="https://x.y")])
    await feed(bot, dp, hidden)
    forwarded = message(BOB, "look", forward_origin=MessageOriginUser(date=datetime.now(UTC), sender_user=ANN))
    await feed(bot, dp, forwarded)
    assert "ссылка" in tg.texts()[0] and "пересылка" in tg.texts()[1]


async def test_admins_and_normal_messages_are_left_alone(env):
    bot, dp, db, tg = env
    await feed(bot, dp, message(ADMIN, "official link https://our.site"))
    await feed(bot, dp, message(BOB, "всем привет!"))
    assert tg.of(DeleteMessage) == [] and tg.of(SendMessage) == []


async def test_flood_mutes(env):
    bot, dp, db, tg = env
    for i in range(6):  # default: more than 5 messages in 10 seconds
        await feed(bot, dp, message(BOB, f"msg {i}"))
    assert "флуд" in tg.texts()[-1]
    assert tg.of(RestrictChatMember)[-1].user_id == BOB.id


async def test_admin_settings_and_stopwords(env):
    bot, dp, db, tg = env
    await feed(bot, dp, message(ADMIN, "/guard links off"))
    assert (await db.get_settings(GROUP.id)).block_links is False
    await feed(bot, dp, message(BOB, "https://now-allowed.example"))
    assert tg.of(DeleteMessage) == []

    await feed(bot, dp, message(ADMIN, "/stop add крипта"))
    await feed(bot, dp, message(BOB, "продаю крипту и крипта дешёвая"))
    assert "стоп-слово «крипта»" in tg.texts()[-1]

    await feed(bot, dp, message(ADMIN, "/guardlog"))
    assert "Последние действия" in tg.texts()[-1]


async def test_non_admin_cannot_change_settings(env):
    bot, dp, db, tg = env
    cmd = message(BOB, "/guard links off")
    await feed(bot, dp, cmd)
    assert (await db.get_settings(GROUP.id)).block_links is True
    assert tg.of(DeleteMessage)[-1].message_id == cmd.message_id


async def test_unwarn_by_reply(env):
    bot, dp, db, tg = env
    await feed(bot, dp, message(BOB, "https://spam.example"))
    await feed(bot, dp, message(ADMIN, "/unwarn", reply_to_message=message(BOB, "hi")))
    assert "Предупреждения сняты" in tg.texts()[-1]
    await feed(bot, dp, message(BOB, "https://spam.example"))
    assert "Предупреждение 1/3" in tg.texts()[-1]  # counter started over
