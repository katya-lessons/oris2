from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

ideas = [
    {
        "id": 1,
        "title": "Learn Flask",
        "description": "Some description",
    },
    {
        "id": 2,
        "title": "Create a portfolio",
        "description": "Make a personal website",
    }
]

@app.route("/")
def index():
    return render_template("index.html", ideas=ideas)


@app.route("/ideas/<int:idea_id>")
def detail(idea_id):
    idea = None

    for item in ideas:
        if item["id"] == idea_id:
            idea = item
            break

    if idea is None:
        return "Idea not found", 404

    return render_template("detail.html", idea=idea)


@app.route("/ideas/add", methods=["GET", "POST"])
def add_idea():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        errors = []

        if not title:
            errors.append("Title is required")

        if not description:
            errors.append("Description is required")
        print(errors)
        if errors:
            return render_template("add.html", errors=errors, title=title, description=description)

        new_idea = {
            "id": len(ideas) + 1,
            "title": title,
            "description": description,
        }

        ideas.append(new_idea)
        return redirect(url_for("index"))

    return render_template("add.html")



if __name__ == "__main__":
    app.run(debug=True)
