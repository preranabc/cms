from app import create_app

app = create_app()

if __name__ == "__main__":
    # For local Windows development, run on port 5000
    app.run(debug=True, host="http://127.0.0.1", port=5000)
