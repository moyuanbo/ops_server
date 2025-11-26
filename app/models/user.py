from datetime import datetime, UTC
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)  # 登录用用户名
    real_name = db.Column(db.String(64), nullable=False)  # 中文姓名（用于显示）
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        """增强密码哈希策略"""
        # 使用更强的哈希参数
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256:100000',  # 100,000次迭代
            salt_length=16
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.now(UTC)

    def __repr__(self):
        return f'<User {self.username} ({self.real_name})>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))