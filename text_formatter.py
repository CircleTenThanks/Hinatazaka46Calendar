import mojimoji
"""
テキストフォーマッターモジュール
"""

def remove_blank(text):
    """
    テキストの空白削除と全角文字を半角に変換する。
    """
    text = text.replace("\n", "").strip()
    text = mojimoji.zen_to_han(text, kana=False)
    return text
