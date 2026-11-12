from app import create_app

from app.routes.ubicacion_routes import ubicacion_bp


app = create_app()

app.register_blueprint(ubicacion_bp)

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5005,
        debug=True
    )