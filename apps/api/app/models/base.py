# apps/api/app/models/base.py
"""SQLAlchemy Base class used across all models.
We use the declarative base from ``sqlalchemy.ext.declarative`` to keep the
definition simple for the prototype. In later milestones we will switch to the
async ``AsyncAttrs`` mixin, but the synchronous version works fine for the
initial migrations and tests.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
