from flask import Blueprint

admin_bp = Blueprint('admin_bp', __name__)  # ✅ correct name

@admin_bp.route("/init-db")
def init_db():
    import seed
    return "✅ Database seeded"