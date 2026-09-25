import pytest

from guard_bot.commands import apply_guard_args, apply_stop_args, describe
from guard_bot.rules import ChatSettings, FloodTracker, find_violation

DEFAULT = ChatSettings()


def check(text="", entities=(), forward=False, settings=DEFAULT):
    return find_violation(text, entities, forward, settings)


@pytest.mark.parametrize(
    "text",
    [
        "go to https://spam.example",
        "http://x.y",
        "www.casino.test",
        "join t.me/spam_channel",
        "best deals on cheap-watches.shop now",
        "Заходи на SPAMSITE.RU",
    ],
)
def test_links_in_text_are_caught(text):
    assert check(text) == "ссылка"


@pytest.mark.parametrize("text", ["привет всем", "версия 3.14 вышла", "см. п. 2.1", "цена 10.5 евро"])
def test_normal_text_passes(text):
    assert check(text) is None


def test_link_entities_are_caught_even_without_visible_url():
    assert check("нажми сюда", entities=["text_link"]) == "ссылка"
    assert check("hi", entities=["bold", "mention"]) is None


def test_forwards():
    assert check("hi", forward=True) == "пересылка"
    assert check("hi", forward=True, settings=DEFAULT.updated(block_forwards=False)) is None


def test_links_can_be_allowed():
    assert check("https://ok.example", settings=DEFAULT.updated(block_links=False)) is None


def test_stopwords_match_whole_words_and_phrases_case_insensitively():
    settings = DEFAULT.updated(stopwords=frozenset({"крипта", "быстрый заработок"}))
    assert check("Лучшая КРИПТА тут", settings=settings) == "стоп-слово «крипта»"
    assert check("Быстрый   заработок без вложений", settings=settings) == "стоп-слово «быстрый заработок»"
    assert check("криптанализ — это наука", settings=settings) is None


def test_settings_roundtrip_ignores_unknown_keys():
    settings = DEFAULT.updated(stopwords=frozenset({"b", "a"}), warn_limit=5)
    data = settings.to_dict()
    assert data["stopwords"] == ["a", "b"]
    assert ChatSettings.from_dict({**data, "future_option": 1}) == settings


def test_flood_tracker():
    flood = FloodTracker()
    hits = [flood.hit(1, 7, now=t, limit=3, seconds=10) for t in (0, 1, 2)]
    assert hits == [False, False, False]
    assert flood.hit(1, 7, now=3, limit=3, seconds=10) is True  # 4th within 10 s
    assert flood.hit(1, 7, now=4, limit=3, seconds=10) is False  # counter reset after the mute
    assert flood.hit(1, 8, now=4, limit=3, seconds=10) is False  # other users are independent


def test_flood_window_slides():
    flood = FloodTracker()
    assert not any(flood.hit(1, 7, now=t, limit=2, seconds=5) for t in (0, 10, 20, 30))


@pytest.mark.parametrize(
    ("args", "field", "value"),
    [
        (["links", "off"], "block_links", False),
        (["forwards", "off"], "block_forwards", False),
        (["captcha", "off"], "captcha", False),
        (["captcha_time", "30"], "captcha_seconds", 30),
        (["warns", "5"], "warn_limit", 5),
        (["mute", "15"], "mute_minutes", 15),
    ],
)
def test_guard_settings(args, field, value):
    new, reply = apply_guard_args(DEFAULT, args)
    assert getattr(new, field) == value and reply


def test_guard_flood_and_help():
    new, _ = apply_guard_args(DEFAULT, ["flood", "3", "20"])
    assert (new.flood_limit, new.flood_seconds) == (3, 20)
    same, text = apply_guard_args(DEFAULT, ["help"])
    assert same == DEFAULT and "/guard links" in text
    assert "Капча" in describe(DEFAULT)


@pytest.mark.parametrize(
    "args",
    [["links", "maybe"], ["captcha_time", "5"], ["flood", "x", "1"], ["warns", "0"], ["teleport", "on"]],
)
def test_guard_rejects_bad_input(args):
    with pytest.raises(ValueError):
        apply_guard_args(DEFAULT, args)


def test_stopword_commands():
    s, _ = apply_stop_args(DEFAULT, ["add", "Быстрый", "Заработок"])
    assert s.stopwords == {"быстрый заработок"}
    _, listing = apply_stop_args(s, ["list"])
    assert "быстрый заработок" in listing
    s, _ = apply_stop_args(s, ["del", "быстрый", "заработок"])
    assert s.stopwords == frozenset()
    with pytest.raises(ValueError):
        apply_stop_args(s, ["del", "нет"])
    with pytest.raises(ValueError):
        apply_stop_args(s, ["add"])
