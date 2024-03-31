#!/usr/bin/env python3

from pass_gn import app, db

app1 = app.app_context()
app1.push()
db.create_all()
