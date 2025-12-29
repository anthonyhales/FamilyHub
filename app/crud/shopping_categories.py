from sqlalchemy import text


def list_categories(db, household_id):
    return db.execute(
        text("""
            SELECT *
            FROM shopping_categories
            WHERE household_id = :hid
            ORDER BY name
        """),
        {"hid": household_id},
    ).fetchall()


def create_category(db, household_id, name, color=None, icon=None):
    db.execute(
        text("""
            INSERT INTO shopping_categories (household_id, name, color, icon)
            VALUES (:hid, :name, :color, :icon)
        """),
        {
            "hid": household_id,
            "name": name,
            "color": color,
            "icon": icon,
        },
    )
    db.commit()
