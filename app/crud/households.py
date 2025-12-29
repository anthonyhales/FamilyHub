from sqlalchemy.orm import Session
from app import models


def get_household_by_name(db: Session, name: str):
    return (
        db.query(models.Household)
        .filter(models.Household.name == name)
        .first()
    )


def create_household(db: Session, name: str):
    hh = models.Household(name=name)
    db.add(hh)
    db.commit()
    db.refresh(hh)
    return hh
