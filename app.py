from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from config import Config
from models import db, User, StoreSetting, Ingredient, Recipe, RecipeIngredient
from auth import login_required, create_user, authenticate_user, get_current_user
from utils import generate_label_pdf, format_currency, format_percentage, validate_positive_number, validate_positive_integer
import io
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# データベースの初期化
db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    """トップページ"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """ユーザー登録"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        store_name = request.form.get('store_name', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # バリデーション
        if not username or not store_name or not password:
            flash('すべての項目を入力してください', 'danger')
            return render_template('register.html')

        if len(username) < 3:
            flash('ユーザーIDは3文字以上で入力してください', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('パスワードは6文字以上で入力してください', 'danger')
            return render_template('register.html')

        if password != password_confirm:
            flash('パスワードが一致しません', 'danger')
            return render_template('register.html')

        # ユーザー作成
        user, error = create_user(username, store_name, password)
        if error:
            flash(error, 'danger')
            return render_template('register.html')

        flash('登録が完了しました。ログインしてください。', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = authenticate_user(username, password)
        if user:
            session['user_id'] = user.id
            session.permanent = True
            flash(f'ようこそ、{user.store_name}さん', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('ユーザーIDまたはパスワードが正しくありません', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """ログアウト"""
    session.clear()
    flash('ログアウトしました', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """ダッシュボード"""
    user = get_current_user()
    recipes = Recipe.query.filter_by(user_id=user.id).all()
    ingredients_count = Ingredient.query.filter_by(user_id=user.id).count()

    # 統計情報を計算
    total_recipes = len(recipes)
    avg_cost_rate = 0.0

    if total_recipes > 0:
        store_setting = StoreSetting.query.filter_by(user_id=user.id).first()
        fixed_cost_per_item = store_setting.get_fixed_cost_per_item() if store_setting else 0.0

        cost_rates = []
        for recipe in recipes:
            cost_rate = recipe.calculate_cost_rate(fixed_cost_per_item)
            cost_rates.append(cost_rate)

        avg_cost_rate = sum(cost_rates) / len(cost_rates)

    return render_template('dashboard.html',
                           user=user,
                           total_recipes=total_recipes,
                           ingredients_count=ingredients_count,
                           avg_cost_rate=avg_cost_rate)


@app.route('/ingredients')
@login_required
def ingredients():
    """材料マスタ一覧"""
    user = get_current_user()
    ingredients_list = Ingredient.query.filter_by(user_id=user.id).order_by(Ingredient.created_at.desc()).all()
    return render_template('ingredients.html', ingredients=ingredients_list)


@app.route('/ingredients/add', methods=['POST'])
@login_required
def add_ingredient():
    """材料追加"""
    user = get_current_user()

    name = request.form.get('name', '').strip()
    unit_price = request.form.get('unit_price', '')
    unit = request.form.get('unit', '').strip()

    # バリデーション
    if not name or not unit:
        flash('材料名と単位を入力してください', 'danger')
        return redirect(url_for('ingredients'))

    unit_price_val, error = validate_positive_number(unit_price, '単価')
    if error:
        flash(error, 'danger')
        return redirect(url_for('ingredients'))

    # 材料を追加
    ingredient = Ingredient(
        user_id=user.id,
        name=name,
        unit_price=unit_price_val,
        unit=unit
    )
    db.session.add(ingredient)
    db.session.commit()

    flash(f'材料「{name}」を追加しました', 'success')
    return redirect(url_for('ingredients'))


@app.route('/ingredients/<int:ingredient_id>/edit', methods=['POST'])
@login_required
def edit_ingredient(ingredient_id):
    """材料編集"""
    user = get_current_user()
    ingredient = Ingredient.query.filter_by(id=ingredient_id, user_id=user.id).first_or_404()

    name = request.form.get('name', '').strip()
    unit_price = request.form.get('unit_price', '')
    unit = request.form.get('unit', '').strip()

    # バリデーション
    if not name or not unit:
        flash('材料名と単位を入力してください', 'danger')
        return redirect(url_for('ingredients'))

    unit_price_val, error = validate_positive_number(unit_price, '単価')
    if error:
        flash(error, 'danger')
        return redirect(url_for('ingredients'))

    # 材料を更新
    ingredient.name = name
    ingredient.unit_price = unit_price_val
    ingredient.unit = unit
    db.session.commit()

    flash(f'材料「{name}」を更新しました', 'success')
    return redirect(url_for('ingredients'))


@app.route('/ingredients/<int:ingredient_id>/delete', methods=['POST'])
@login_required
def delete_ingredient(ingredient_id):
    """材料削除"""
    user = get_current_user()
    ingredient = Ingredient.query.filter_by(id=ingredient_id, user_id=user.id).first_or_404()

    # レシピで使用されているかチェック
    if ingredient.recipe_ingredients:
        flash(f'材料「{ingredient.name}」はレシピで使用されているため削除できません', 'warning')
        return redirect(url_for('ingredients'))

    name = ingredient.name
    db.session.delete(ingredient)
    db.session.commit()

    flash(f'材料「{name}」を削除しました', 'success')
    return redirect(url_for('ingredients'))


@app.route('/recipes')
@login_required
def recipes():
    """レシピ一覧"""
    user = get_current_user()
    recipes_list = Recipe.query.filter_by(user_id=user.id).order_by(Recipe.updated_at.desc()).all()

    # 固定費設定を取得
    store_setting = StoreSetting.query.filter_by(user_id=user.id).first()
    fixed_cost_per_item = store_setting.get_fixed_cost_per_item() if store_setting else 0.0

    # 各レシピの計算結果を準備
    recipe_data = []
    for recipe in recipes_list:
        recipe_data.append({
            'recipe': recipe,
            'material_cost': recipe.calculate_material_cost(),
            'cost_per_item': recipe.calculate_cost_per_item(fixed_cost_per_item),
            'cost_rate': recipe.calculate_cost_rate(fixed_cost_per_item),
            'profit': recipe.calculate_profit(fixed_cost_per_item),
            'profit_rate': recipe.calculate_profit_rate(fixed_cost_per_item)
        })

    return render_template('recipes.html', recipe_data=recipe_data)


@app.route('/recipes/new')
@login_required
def new_recipe():
    """レシピ新規作成フォーム"""
    user = get_current_user()
    ingredients_list = Ingredient.query.filter_by(user_id=user.id).order_by(Ingredient.name).all()

    if not ingredients_list:
        flash('まず材料マスタに材料を登録してください', 'warning')
        return redirect(url_for('ingredients'))

    return render_template('recipe_form.html', recipe=None, ingredients_list=ingredients_list)


@app.route('/recipes/add', methods=['POST'])
@login_required
def add_recipe():
    """レシピ追加"""
    user = get_current_user()

    product_name = request.form.get('product_name', '').strip()
    selling_price = request.form.get('selling_price', '')
    production_quantity = request.form.get('production_quantity', '')

    # バリデーション
    if not product_name:
        flash('商品名を入力してください', 'danger')
        return redirect(url_for('new_recipe'))

    selling_price_val, error = validate_positive_number(selling_price, '販売価格')
    if error:
        flash(error, 'danger')
        return redirect(url_for('new_recipe'))

    production_quantity_val, error = validate_positive_integer(production_quantity, '製造個数')
    if error or production_quantity_val == 0:
        flash('製造個数は1以上の整数を入力してください', 'danger')
        return redirect(url_for('new_recipe'))

    # レシピを作成
    recipe = Recipe(
        user_id=user.id,
        product_name=product_name,
        selling_price=selling_price_val,
        production_quantity=production_quantity_val
    )
    db.session.add(recipe)
    db.session.flush()  # recipe.idを取得するため

    # 材料を追加
    ingredient_ids = request.form.getlist('ingredient_id[]')
    quantities = request.form.getlist('quantity[]')

    if not ingredient_ids or not quantities:
        db.session.rollback()
        flash('材料を1つ以上追加してください', 'danger')
        return redirect(url_for('new_recipe'))

    for ingredient_id, quantity in zip(ingredient_ids, quantities):
        if not ingredient_id or not quantity:
            continue

        # 材料の所有権を確認
        ingredient = Ingredient.query.filter_by(id=int(ingredient_id), user_id=user.id).first()
        if not ingredient:
            db.session.rollback()
            flash('無効な材料が含まれています', 'danger')
            return redirect(url_for('new_recipe'))

        quantity_val, error = validate_positive_number(quantity, '使用量')
        if error:
            db.session.rollback()
            flash(error, 'danger')
            return redirect(url_for('new_recipe'))

        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=int(ingredient_id),
            quantity=quantity_val
        )
        db.session.add(recipe_ingredient)

    db.session.commit()
    flash(f'レシピ「{product_name}」を追加しました', 'success')
    return redirect(url_for('recipes'))


@app.route('/recipes/<int:recipe_id>/edit')
@login_required
def edit_recipe(recipe_id):
    """レシピ編集フォーム"""
    user = get_current_user()
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=user.id).first_or_404()
    ingredients_list = Ingredient.query.filter_by(user_id=user.id).order_by(Ingredient.name).all()

    return render_template('recipe_form.html', recipe=recipe, ingredients_list=ingredients_list)


@app.route('/recipes/<int:recipe_id>/update', methods=['POST'])
@login_required
def update_recipe(recipe_id):
    """レシピ更新"""
    user = get_current_user()
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=user.id).first_or_404()

    product_name = request.form.get('product_name', '').strip()
    selling_price = request.form.get('selling_price', '')
    production_quantity = request.form.get('production_quantity', '')

    # バリデーション
    if not product_name:
        flash('商品名を入力してください', 'danger')
        return redirect(url_for('edit_recipe', recipe_id=recipe_id))

    selling_price_val, error = validate_positive_number(selling_price, '販売価格')
    if error:
        flash(error, 'danger')
        return redirect(url_for('edit_recipe', recipe_id=recipe_id))

    production_quantity_val, error = validate_positive_integer(production_quantity, '製造個数')
    if error or production_quantity_val == 0:
        flash('製造個数は1以上の整数を入力してください', 'danger')
        return redirect(url_for('edit_recipe', recipe_id=recipe_id))

    # レシピを更新
    recipe.product_name = product_name
    recipe.selling_price = selling_price_val
    recipe.production_quantity = production_quantity_val
    recipe.updated_at = datetime.utcnow()

    # 既存の材料を削除
    RecipeIngredient.query.filter_by(recipe_id=recipe.id).delete()

    # 材料を再追加
    ingredient_ids = request.form.getlist('ingredient_id[]')
    quantities = request.form.getlist('quantity[]')

    if not ingredient_ids or not quantities:
        db.session.rollback()
        flash('材料を1つ以上追加してください', 'danger')
        return redirect(url_for('edit_recipe', recipe_id=recipe_id))

    for ingredient_id, quantity in zip(ingredient_ids, quantities):
        if not ingredient_id or not quantity:
            continue

        # 材料の所有権を確認
        ingredient = Ingredient.query.filter_by(id=int(ingredient_id), user_id=user.id).first()
        if not ingredient:
            db.session.rollback()
            flash('無効な材料が含まれています', 'danger')
            return redirect(url_for('edit_recipe', recipe_id=recipe_id))

        quantity_val, error = validate_positive_number(quantity, '使用量')
        if error:
            db.session.rollback()
            flash(error, 'danger')
            return redirect(url_for('edit_recipe', recipe_id=recipe_id))

        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=int(ingredient_id),
            quantity=quantity_val
        )
        db.session.add(recipe_ingredient)

    db.session.commit()
    flash(f'レシピ「{product_name}」を更新しました', 'success')
    return redirect(url_for('recipes'))


@app.route('/recipes/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    """レシピ削除"""
    user = get_current_user()
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=user.id).first_or_404()

    product_name = recipe.product_name
    db.session.delete(recipe)
    db.session.commit()

    flash(f'レシピ「{product_name}」を削除しました', 'success')
    return redirect(url_for('recipes'))


@app.route('/recipes/<int:recipe_id>/label')
@login_required
def recipe_label(recipe_id):
    """ラベル生成ページ"""
    user = get_current_user()
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=user.id).first_or_404()
    return render_template('label.html', recipe=recipe, now=datetime.now())


@app.route('/recipes/<int:recipe_id>/label/pdf')
@login_required
def download_label_pdf(recipe_id):
    """ラベルPDFをダウンロード"""
    user = get_current_user()
    recipe = Recipe.query.filter_by(id=recipe_id, user_id=user.id).first_or_404()

    include_price = request.args.get('include_price', 'true') == 'true'
    include_date = request.args.get('include_date', 'true') == 'true'

    pdf_data = generate_label_pdf(recipe, include_price, include_date)

    return send_file(
        io.BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'label_{recipe.product_name}.pdf'
    )


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """店舗設定"""
    user = get_current_user()
    store_setting = StoreSetting.query.filter_by(user_id=user.id).first()

    if request.method == 'POST':
        fixed_cost_enabled = request.form.get('fixed_cost_enabled') == 'on'
        monthly_fixed_cost = request.form.get('monthly_fixed_cost', '0')
        monthly_production = request.form.get('monthly_production', '0')

        # バリデーション
        monthly_fixed_cost_val, error = validate_positive_number(monthly_fixed_cost, '月額固定費')
        if error:
            flash(error, 'danger')
            return render_template('settings.html', user=user, store_setting=store_setting)

        monthly_production_val, error = validate_positive_integer(monthly_production, '月間生産個数')
        if error:
            flash(error, 'danger')
            return render_template('settings.html', user=user, store_setting=store_setting)

        # 設定を更新
        store_setting.fixed_cost_enabled = fixed_cost_enabled
        store_setting.monthly_fixed_cost = monthly_fixed_cost_val
        store_setting.monthly_production = monthly_production_val
        db.session.commit()

        flash('設定を更新しました', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', user=user, store_setting=store_setting)


# テンプレートフィルター
@app.template_filter('currency')
def currency_filter(amount):
    """通貨フォーマット"""
    return format_currency(amount)


@app.template_filter('percentage')
def percentage_filter(value):
    """パーセンテージフォーマット"""
    return format_percentage(value)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
