app/
├── main.py
├── auth/
│   ├── __init__.py
│   ├── dependencies.py  # JWT authentication
│   └── models.py        # Auth models
├── todos/
│   ├── __init__.py
│   ├── routes.py        # Todo API endpoints
│   ├── models.py        # Pydantic models for Todo
│   └── repository.py    # MongoDB operations
└── core/
    ├── __init__.py
    ├── config.py        # App configuration
    ├── database.py      # MongoDB connection
    └── errors.py        # Error handling