# -*- coding: utf-8 -*-
"""
================================================================================
DATABASE BASE
================================================================================
Bazna klasa za SQLAlchemy modele.

Verzija: 1.0.0
================================================================================
"""

from sqlalchemy.ext.declarative import declarative_base

# Kreiranje bazne klase za sve modele
Base = declarative_base()
