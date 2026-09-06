from app.area_hints import guess_area_from_text


def test_guesses_garage_from_declined_form():
    result = guess_area_from_text("malowanie garazu")
    assert result is not None
    assert result["area_m2"] == 15.0
    assert "garaż" in result["label"]


def test_guesses_bathroom_with_diacritics():
    result = guess_area_from_text("ułożenie płytek w łazience")
    assert result is not None
    assert result["area_m2"] == 5.0


def test_no_match_returns_none():
    assert guess_area_from_text("jakiś ogólny opis bez konkretów") is None


def test_word_boundary_avoids_false_positive_substring():
    # "salonik" contains "salon" as a substring but is a different word —
    # must not match on substring, only on the whole word.
    assert guess_area_from_text("mam salonik dla lalek") is None


def test_explicit_area_should_not_be_overridden_by_caller():
    # This module only guesses; it's the caller's job to only use the guess
    # when area_m2 is otherwise missing. Verify the guess itself is stable
    # and doesn't depend on any other field being present.
    result = guess_area_from_text("malowanie garazu 30m2")
    assert result is not None
    assert result["area_m2"] == 15.0  # module always returns its own default
