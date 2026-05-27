import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class URLMap(db.Model):
    __tablename__ = 'urls'

    id         = db.Column(db.Integer, primary_key=True)
    long_url   = db.Column(db.String(2048), nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    clicks = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<URLMap {self.short_code} -> {self.long_url[:30]}>"
