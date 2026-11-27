
from app.extensions.database import db


class Categoria(db.Model):

    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True)
    activo = db.Column(db.Boolean, default=True)
    icono = db.Column(db.String(100))

    servicios = db.relationship("Servicio", back_populates="categoria")
    
    perfiles = db.relationship(
        "PerfilProfesional",
        secondary="perfil_categorias",
        back_populates="categorias"
    )
