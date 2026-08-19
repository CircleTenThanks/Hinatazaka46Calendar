import mojimoji
"""
テキストフォーマッターモジュール
"""

def remove_blank(text: str) -> str:
    """
    テキストの空白削除と全角文字を半角に変換する。
    
    Args:
        text (str): 処理対象のテキスト
    
    Returns:
        str: 処理後のテキスト
    """
    text = text.replace("\n", "").strip()
    text = mojimoji.zen_to_han(text, kana=False)
    return text