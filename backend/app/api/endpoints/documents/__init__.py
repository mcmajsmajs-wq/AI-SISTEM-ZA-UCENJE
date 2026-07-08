# -*- coding: utf-8 -*-
"""
================================================================================
DOCUMENTS ENDPOINTS PACKAGE
================================================================================
Modularized package containing all document-related endpoints.
================================================================================
"""

from fastapi import APIRouter

router = APIRouter()

from .crud import *
from .processing import *
from .translation import *
from .progress import *
from .chunks import *
from .pipeline import *
from .export_sync import *
from .quiz_availability import *
from .export_async_docx import *
from .export_async_pdf import *
