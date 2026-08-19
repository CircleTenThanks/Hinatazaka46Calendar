# Copyright (c) 2020 ddn
# Copyright (c) 2026 CircleTenThanks
# 一部は https://qiita.com/ddn/items/42def5fa721e531eecdb を基に改変している.
"""テキストの空白削除と全角・半角変換を行う."""

import mojimoji


def remove_blank(text: str) -> str:
    """テキストの空白削除と全角文字を半角に変換する.

    Args:
        text: 処理対象のテキスト。

    Returns:
        処理後のテキスト。
    """
    text = text.replace("\n", "").strip()
    return mojimoji.zen_to_han(text, kana=False)
