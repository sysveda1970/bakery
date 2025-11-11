from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """ユーザー(店舗)テーブル"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    store_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # リレーションシップ
    store_setting = db.relationship('StoreSetting', backref='user', uselist=False, cascade='all, delete-orphan')
    ingredients = db.relationship('Ingredient', backref='user', cascade='all, delete-orphan')
    recipes = db.relationship('Recipe', backref='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'


class StoreSetting(db.Model):
    """店舗設定テーブル"""
    __tablename__ = 'store_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    fixed_cost_enabled = db.Column(db.Boolean, default=False)
    monthly_fixed_cost = db.Column(db.Float, default=0.0)
    monthly_production = db.Column(db.Integer, default=0)

    def get_fixed_cost_per_item(self):
        """商品1個あたりの固定費配賦額を計算"""
        if not self.fixed_cost_enabled or self.monthly_production == 0:
            return 0.0
        return self.monthly_fixed_cost / self.monthly_production

    def __repr__(self):
        return f'<StoreSetting user_id={self.user_id}>'


class Ingredient(db.Model):
    """材料マスタテーブル"""
    __tablename__ = 'ingredients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # g, ml, 個 等
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # リレーションシップ
    recipe_ingredients = db.relationship('RecipeIngredient', backref='ingredient', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Ingredient {self.name}>'


class Recipe(db.Model):
    """レシピテーブル"""
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    production_quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションシップ
    recipe_ingredients = db.relationship('RecipeIngredient', backref='recipe', cascade='all, delete-orphan')

    def calculate_material_cost(self):
        """材料費の合計を計算"""
        total = 0.0
        for ri in self.recipe_ingredients:
            total += ri.calculate_cost()
        return total

    def calculate_cost_per_item(self, fixed_cost_per_item=0.0):
        """1個あたりの原価を計算(固定費含む)"""
        material_cost = self.calculate_material_cost()
        total_cost = material_cost + (fixed_cost_per_item * self.production_quantity)
        return total_cost / self.production_quantity if self.production_quantity > 0 else 0.0

    def calculate_cost_rate(self, fixed_cost_per_item=0.0):
        """原価率を計算(%)"""
        cost_per_item = self.calculate_cost_per_item(fixed_cost_per_item)
        if self.selling_price == 0:
            return 0.0
        return (cost_per_item / self.selling_price) * 100

    def calculate_profit(self, fixed_cost_per_item=0.0):
        """利益額を計算"""
        cost_per_item = self.calculate_cost_per_item(fixed_cost_per_item)
        return self.selling_price - cost_per_item

    def calculate_profit_rate(self, fixed_cost_per_item=0.0):
        """利益率を計算(%)"""
        profit = self.calculate_profit(fixed_cost_per_item)
        if self.selling_price == 0:
            return 0.0
        return (profit / self.selling_price) * 100

    def __repr__(self):
        return f'<Recipe {self.product_name}>'


class RecipeIngredient(db.Model):
    """レシピ材料テーブル(中間テーブル)"""
    __tablename__ = 'recipe_ingredients'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # 使用量

    def calculate_cost(self):
        """この材料の費用を計算"""
        return self.quantity * self.ingredient.unit_price

    def __repr__(self):
        return f'<RecipeIngredient recipe_id={self.recipe_id} ingredient_id={self.ingredient_id}>'
