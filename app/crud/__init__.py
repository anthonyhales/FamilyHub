"""CRUD package.

Important: this project previously had an app/crud.py module.
To avoid import ambiguity, all CRUD is exposed from this package.
"""

from .households import get_household_by_name, create_household

from .users import (
    get_user,
    get_user_by_email,
    list_users,
    create_user,
    authenticate_user,
    set_user_password,
    set_user_admin,
    set_user_active,
)

from .sessions import create_session, get_session_by_token, delete_session

from .calendar import list_upcoming_events
from .chores import list_chores, last_completed_on
from .mealplan import list_meals_in_range

from .shopping_categories import list_categories, create_category
from .shopping import (
    list_shops,
    create_shop,
    list_lists,
    get_list,
    create_list,
    archive_list,
    list_items,
    add_item,
    get_item,
    toggle_item,
    delete_item,
    count_open_items,
)

__all__ = [
    # households
    "get_household_by_name",
    "create_household",
    # users
    "get_user",
    "get_user_by_email",
    "list_users",
    "create_user",
    "authenticate_user",
    "set_user_password",
    "set_user_admin",
    "set_user_active",
    # sessions
    "create_session",
    "get_session_by_token",
    "delete_session",
    # calendar
    "list_upcoming_events",
    # chores
    "list_chores",
    "last_completed_on",
    # mealplan
    "list_meals_in_range",
    # shopping categories
    "list_categories",
    "create_category",
    # shopping
    "list_shops",
    "create_shop",
    "list_lists",
    "get_list",
    "create_list",
    "archive_list",
    "list_items",
    "add_item",
    "get_item",
    "toggle_item",
    "delete_item",
    "count_open_items",
]

