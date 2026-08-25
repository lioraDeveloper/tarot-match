"""Demo seekers so a fresh install can match immediately."""

from __future__ import annotations

from app import db
from app.auth import hash_password
from app.tarot import interpret_spread

SEED_USERS = [
    {
        "email": "nova@demo.local",
        "password": "demo1234",
        "name": "Nova",
        "birth_date": "1996-04-12",
        "gender": "woman",
        "looking_for_gender": ["man", "nonbinary"],
        "min_age_preference": 26,
        "max_age_preference": 40,
        "bio": "Night swims, vinyl, and people who mean what they say.",
        "cards": [18, 6, 17],
    },
    {
        "email": "orion@demo.local",
        "password": "demo1234",
        "name": "Orion",
        "birth_date": "1992-11-03",
        "gender": "man",
        "looking_for_gender": ["woman"],
        "min_age_preference": 24,
        "max_age_preference": 36,
        "bio": "Architect by day, stargazer by habit.",
        "cards": [9, 1, 19],
    },
    {
        "email": "lumen@demo.local",
        "password": "demo1234",
        "name": "Lumen",
        "birth_date": "1998-07-21",
        "gender": "nonbinary",
        "looking_for_gender": ["any"],
        "min_age_preference": 25,
        "max_age_preference": 38,
        "bio": "I collect first sentences and last trains.",
        "cards": [2, 14, 21],
    },
    {
        "email": "sol@demo.local",
        "password": "demo1234",
        "name": "Sol",
        "birth_date": "1994-01-30",
        "gender": "man",
        "looking_for_gender": ["woman", "nonbinary"],
        "min_age_preference": 25,
        "max_age_preference": 39,
        "bio": "Cooks too much food. Believes in second chances.",
        "cards": [19, 8, 6],
    },
    {
        "email": "iris@demo.local",
        "password": "demo1234",
        "name": "Iris",
        "birth_date": "1997-09-08",
        "gender": "woman",
        "looking_for_gender": ["woman", "nonbinary"],
        "min_age_preference": 24,
        "max_age_preference": 38,
        "bio": "Museum benches, strong tea, slow-burn conversation.",
        "cards": [3, 2, 17],
    },
    {
        "email": "kai@demo.local",
        "password": "demo1234",
        "name": "Kai",
        "birth_date": "1991-05-16",
        "gender": "man",
        "looking_for_gender": ["any"],
        "min_age_preference": 27,
        "max_age_preference": 42,
        "bio": "Sailing instructor. Terrible at small talk, excellent at weather.",
        "cards": [7, 13, 10],
    },
    {
        "email": "mira@demo.local",
        "password": "demo1234",
        "name": "Mira",
        "birth_date": "1995-12-02",
        "gender": "woman",
        "looking_for_gender": ["man"],
        "min_age_preference": 28,
        "max_age_preference": 40,
        "bio": "Therapist off-duty. I still want mystery.",
        "cards": [12, 11, 14],
    },
    {
        "email": "ash@demo.local",
        "password": "demo1234",
        "name": "Ash",
        "birth_date": "1993-08-19",
        "gender": "nonbinary",
        "looking_for_gender": ["woman", "man"],
        "min_age_preference": 25,
        "max_age_preference": 37,
        "bio": "Poet with a day job in lighting design.",
        "cards": [15, 8, 20],
    },
]


def seed_if_empty() -> None:
    if db.user_count() > 0:
        return
    for item in SEED_USERS:
        reading = interpret_spread(item["cards"])
        db.create_user(
            email=item["email"],
            password_hash=hash_password(item["password"]),
            name=item["name"],
            birth_date=item["birth_date"],
            gender=item["gender"],
            looking_for_gender=item["looking_for_gender"],
            min_age_preference=item["min_age_preference"],
            max_age_preference=item["max_age_preference"],
            bio=item["bio"],
            energy_signature=reading["energy_signature"],
            last_spread=reading["last_spread"],
        )
