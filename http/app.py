import itertools
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

notes = []
note_ids = itertools.count(1)

def find_note(note_id):
    return next((n for n in notes if n["id"] == note_id), None)

@app.get("/")
def index():
    return "<h1>Гостевая книга</h1>"

@app.get("/notes")
def list_notes():
    return jsonify(notes)

@app.post("/notes")
def create_note():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("text"), str) or not data["text"].strip():
        return jsonify(error="field 'text' (non-empty string) is required"), 400
    note = {"id": next(note_ids), "text": data["text"].strip()}
    notes.append(note)
    return jsonify(note), 201

@app.get("/notes/<int:note_id>")
def get_note(note_id):
    note = find_note(note_id)
    if note is None:
        abort(404)
    return jsonify(note)

@app.delete("/notes/<int:note_id>")
def delete_note(note_id):
    note = find_note(note_id)
    if note is None:
        abort(404)
    notes.remove(note)
    return "", 204

@app.errorhandler(404)
def not_found(error):
    return jsonify(error="not found"), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify(error="method not allowed"), 405

if __name__ == "__main__":
    app.run(debug=True)
