from __future__ import annotations

from typing import Literal, Tuple

CompatibilityVerdict = Literal[
    "likely_compatible",
    "unknown",
    "likely_incompatible",
]

_LIKELY_COMPATIBLE_IPHONE_TOKENS = [
    "iphone xs",
    "iphone xr",
    "iphone 11",
    "iphone 12",
    "iphone 13",
    "iphone 14",
    "iphone 15",
    "iphone se (2020)",
    "iphone se (2022)",
]

_LIKELY_INCOMPATIBLE_IPHONE_TOKENS = [
    "iphone 6",
    "iphone 6s",
    "iphone 7",
    "iphone 8",
    "iphone se",
]

_ANDROID_COMPATIBLE_TOKENS = [
    "pixel 3",
    "pixel 4",
    "pixel 5",
    "pixel 6",
    "pixel 7",
    "pixel 8",
    "sm-g99",  # Samsung Galaxy S23 series partial UA token
    "sm-s91",  # Samsung Galaxy S22/S23 variations
    "sm-s92",
]

_ANDROID_LIKELY_INCOMPATIBLE_TOKENS = [
    "sm-g95",  # Galaxy S8
    "sm-g96",  # Galaxy S9
]


def classify_user_agent(user_agent: str | None) -> Tuple[CompatibilityVerdict, str]:
    if not user_agent:
        return (
            "unknown",
            "We could not detect your device. You can double-check compatibility from your settings.",
        )

    ua = user_agent.lower()

    # iPhone heuristics
    if "iphone" in ua:
        if any(token in ua for token in _LIKELY_COMPATIBLE_IPHONE_TOKENS):
            return (
                "likely_compatible",
                "Most recent iPhone models support eSIM out of the box.",
            )
        if any(token in ua for token in _LIKELY_INCOMPATIBLE_IPHONE_TOKENS):
            return (
                "likely_incompatible",
                "Older iPhones before XS typically do not support eSIM.",
            )
        return (
            "unknown",
            "We detected an iPhone but could not confirm the specific model.",
        )

    # Android heuristics
    if "android" in ua or "pixel" in ua or "sm-" in ua:
        if any(token in ua for token in _ANDROID_COMPATIBLE_TOKENS):
            return (
                "likely_compatible",
                "Recent Android flagships (Pixel, Samsung Galaxy S22+) support eSIM.",
            )
        if any(token in ua for token in _ANDROID_LIKELY_INCOMPATIBLE_TOKENS):
            return (
                "likely_incompatible",
                "This Android device line typically predates widespread eSIM support.",
            )
        if "android 13" in ua or "android 14" in ua:
            return (
                "likely_compatible",
                "Android 13+ usually ships with eSIM support enabled.",
            )
        return (
            "unknown",
            "Android device detected. Please confirm eSIM support in system settings.",
        )

    return (
        "unknown",
        "We could not match your device to our compatibility list. Please verify manually.",
    )
