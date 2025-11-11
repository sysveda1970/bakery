from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import io
import os
from datetime import datetime


def setup_japanese_font(c):
    """日本語フォントをセットアップ"""
    try:
        # Windowsの日本語フォントを登録
        font_paths = [
            "C:/Windows/Fonts/msgothic.ttc",  # MSゴシック
            "C:/Windows/Fonts/msmincho.ttc",  # MS明朝
            "C:/Windows/Fonts/meiryo.ttc",    # メイリオ
            "C:/Windows/Fonts/YuGothM.ttc",   # 游ゴシック Medium
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                # TTCファイルの場合は最初のフォントを使用
                pdfmetrics.registerFont(TTFont('Japanese', font_path, subfontIndex=0))
                return 'Japanese'

        # フォントが見つからない場合はHelveticaを使用（英数字のみ）
        return 'Helvetica'
    except Exception as e:
        print(f"Font registration error: {e}")
        return 'Helvetica'


def generate_label_pdf(recipe, include_price=True, include_date=True):
    """
    商品ラベルのPDFを生成

    Args:
        recipe: Recipeオブジェクト
        include_price: 販売価格を含めるか
        include_date: 製造日を含めるか

    Returns:
        PDFデータ(bytes)
    """
    buffer = io.BytesIO()

    # A4サイズ(210mm x 297mm)
    width, height = A4

    # PDFキャンバスの作成
    c = canvas.Canvas(buffer, pagesize=A4)

    # 日本語フォントのセットアップ
    font_name = setup_japanese_font(c)

    # ラベルのサイズと配置(60mm x 40mm のラベルを想定)
    label_width = 60 * mm
    label_height = 40 * mm
    margin_x = 15 * mm
    margin_y = 20 * mm

    # 位置設定
    x = margin_x
    y = height - margin_y - label_height

    # 枠線を描画
    c.rect(x, y, label_width, label_height)

    # テキストの開始位置
    text_x = x + 5 * mm
    text_y = y + label_height - 8 * mm
    line_height = 4 * mm

    # 商品名(太字・大きめ)
    c.setFont(font_name, 14)
    c.drawString(text_x, text_y, recipe.product_name)
    text_y -= line_height * 1.5

    # 原材料表示
    c.setFont(font_name, 9)
    c.drawString(text_x, text_y, "【原材料】")
    text_y -= line_height

    # 材料リストを取得
    ingredients_list = []
    for ri in recipe.recipe_ingredients:
        ingredients_list.append(ri.ingredient.name)

    # 材料を表示(複数行に分割)
    c.setFont(font_name, 8)
    ingredients_text = "、".join(ingredients_list)

    # 長い場合は複数行に分割
    max_width = label_width - 10 * mm
    if c.stringWidth(ingredients_text, font_name, 8) > max_width:
        words = ingredients_list
        line = ""
        for word in words:
            test_line = line + word + "、" if line else word
            if c.stringWidth(test_line, font_name, 8) < max_width:
                line = test_line
            else:
                if line:
                    c.drawString(text_x, text_y, line.rstrip("、"))
                    text_y -= line_height * 0.8
                line = word + "、"
        if line:
            c.drawString(text_x, text_y, line.rstrip("、"))
            text_y -= line_height
    else:
        c.drawString(text_x, text_y, ingredients_text)
        text_y -= line_height * 1.2

    # 販売価格
    if include_price:
        c.setFont(font_name, 11)
        text_y -= line_height * 0.5
        price_text = f"¥{int(recipe.selling_price):,}"
        c.drawString(text_x, text_y, price_text)
        text_y -= line_height

    # 製造日
    if include_date:
        c.setFont(font_name, 8)
        today = datetime.now().strftime("%Y年%m月%d日")
        c.drawString(text_x, text_y, f"製造日: {today}")

    # PDFを保存
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.getvalue()


def format_currency(amount):
    """金額を日本円形式でフォーマット"""
    return f"¥{int(amount):,}"


def format_percentage(value):
    """パーセンテージをフォーマット"""
    return f"{value:.1f}%"


def validate_positive_number(value, field_name="値"):
    """正の数値かどうかを検証"""
    try:
        num = float(value)
        if num < 0:
            return None, f"{field_name}は0以上の数値を入力してください"
        return num, None
    except (ValueError, TypeError):
        return None, f"{field_name}は有効な数値を入力してください"


def validate_positive_integer(value, field_name="値"):
    """正の整数かどうかを検証"""
    try:
        num = int(value)
        if num < 0:
            return None, f"{field_name}は0以上の整数を入力してください"
        return num, None
    except (ValueError, TypeError):
        return None, f"{field_name}は有効な整数を入力してください"
