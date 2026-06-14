# -*- coding: utf-8 -*-
"""
===============================================================================
QUIZ GENERATION MODULE
===============================================================================

Centralizovana logika za generisanje kviz pitanja sa per-provider timeout override-om.

Verzija: 1.0.0
===============================================================================
"""

import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

PER_PROVIDER_TIMEOUT = 45


def generate_with_prompt(
    client, prompt: str, num_questions: int
) -> Tuple[bool, str, str]:
    """
    Generiše kviz pitanja override-ujući client.timeout na PER_PROVIDER_TIMEOUT.

    Obezbeđuje da svaki provider ima konzistentan timeout bez obzira na
    individualna podešavanja. Restore-uje originalni timeout posle poziva.

    Args:
        client: Instanca quiz klijenta (mora imati .timeout i .generate())
        prompt: Prompt za generisanje
        num_questions: Broj pitanja

    Returns:
        Tuple[bool, str, str]: (success, raw_json_string, error)
    """
    original_timeout = getattr(client, "timeout", None)
    try:
        if hasattr(client, "timeout"):
            client.timeout = PER_PROVIDER_TIMEOUT
        return client.generate(prompt, num_questions)
    finally:
        if original_timeout is not None and hasattr(client, "timeout"):
            client.timeout = original_timeout
