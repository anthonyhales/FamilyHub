"""
CRUD package.
This package contains all the Create, Read, Update, and Delete operations
for the application.
"""

# households
from .households import (
    get_household_by_name,
    create_household,
)

# users
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

# sessions
from .sessions import (
    create_session,
    get_session_by_token,
    delete_session,
)

# calendar
from .calendar import (
    list_upcoming_events,
    create_event,
)

# chores
from .chores import (
    list_chores,
    create_chore,
    last_completed_on,
)

# mealplan
from .mealplan import (
    upsert_meal,
    list_meals_in_range,
)

# shopping categories
from .shopping_categories import (
    list_categories,
    create_category,
)

# shopping
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
    "create_event",

    # chores
    "list_chores",
    "create_chore",
    "last_completed_on",

    # mealplan
    "upsert_meal",
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
