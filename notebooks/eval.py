from fasthtml.common import (
    fast_app,
    serve,
    Main,
    H1,
    Article,
    Div,
    Form,
    Textarea,
    NotStr,
    Button,
    H2,
    A,
    RedirectResponse,
    Hidden,
    Strong,
    database,
)

import mistletoe
from dataclasses import dataclass
import urllib

import json


db = database("eval_6.db")


notes = db.t.notes

if notes not in db.t:
    notes = notes.create(dict(idx=int, note=str), pk="idx")

Note = notes.dataclass()

app, rt = fast_app()

with open("results_6.json") as f:
    data = json.load(f)


@rt("/annotate/{idx}")
def get(idx: int):
    row = data[idx]

    @rt
    def save_note(idx: int, note: str):
        notes.insert(Note(idx=idx, note=note))
        return note

    try:
        note = notes[idx].note
    except:
        note = ""

    return Main(cls="container")(
        H1("Data Explorer"),
        Div(cls="grid")(
            Article(
                Div(style="margin-bottom: 18px")(Strong("User Query: "), row["query"]),
                Div(style="margin-bottom: 18px")(
                    Strong("Search Terms: "),
                    *[
                        A(
                            term,
                            target="_blank",
                            style="display: block",
                            href=f"https://radiopaedia.org/search?scope=articles&commit=Search&q={urllib.parse.quote_plus(term)}",
                        )
                        for term in row["search_terms"]
                    ],
                ),
                Div(
                    *[
                        A(url, style="display: block", href=url, target="_blank")
                        for url in row["urls"]
                    ]
                    if "urls" in row
                    else []
                ),
            ),
            Article(style="max-height: 600px; overflow: scroll;")(
                H2("Answer"),
                NotStr(mistletoe.markdown(row["answer"]))
                if "answer" in row
                else "Error",
            ),
            Article(
                H2("Notes"),
                Form(hx_post=save_note.to(), hx_target="#note")(
                    Textarea(rows=10, id="note")(note),
                    Hidden(name="idx", value=idx),
                    Button(type="submit")("Save Note"),
                ),
            ),
        ),
        Div(cls="grid")(
            A(href=f"/annotate/{idx - 1}", role="button")("Previous"),
            A(href=f"/annotate/{idx + 1}", role="button")("Next"),
        ),
    )


@rt("/")
def get():  # noqa: F811
    return RedirectResponse("/annotate/0")


@rt("/all_notes")
def get():  # noqa: F811
    _notes = notes(limit=2)

    return Main(cls="container")(
        H1("Notes"),
        Div(
            *[
                Div(
                    A(
                        row.idx,
                        href=f"/{row.idx}",
                        style="display: block",
                        target="_blank",
                    ),
                    row.note,
                )
                for row in _notes
            ]
        ),
    )


serve()
