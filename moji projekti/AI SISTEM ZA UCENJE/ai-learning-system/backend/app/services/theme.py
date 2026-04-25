# -*- coding: utf-8 -*-
"""
===============================================================================
THEME SERVICE
===============================================================================
Servis za upravljanje temama (Light/Dark mode).

Verzija: 1.0.0
===============================================================================
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ThemeColors:
    """Boje teme."""
    primary: str
    primary_hover: str
    secondary: str
    background: str
    surface: str
    text: str
    text_secondary: str
    border: str
    success: str
    warning: str
    error: str
    info: str


LIGHT_THEME = ThemeColors(
    primary="#1e40af",
    primary_hover="#1e3a8a",
    secondary="#64748b",
    background="#f8fafc",
    surface="#ffffff",
    text="#0f172a",
    text_secondary="#64748b",
    border="#e2e8f0",
    success="#16a34a",
    warning="#d97706",
    error="#dc2626",
    info="#0284c7",
)

DARK_THEME = ThemeColors(
    primary="#3b82f6",
    primary_hover="#60a5fa",
    secondary="#94a3b8",
    background="#0f172a",
    surface="#1e293b",
    text="#f1f5f9",
    text_secondary="#94a3b8",
    border="#334155",
    success="#22c55e",
    warning="#f59e0b",
    error="#ef4444",
    info="#0ea5e9",
)


class ThemeService:
    """
    ================================================================================
    THEME SERVICE
    ================================================================================
    Servis za upravljanje temama aplikacije.
    ================================================================================
    """
    
    def __init__(self):
        """Inicijalizuje theme servis."""
        self.themes = {
            'light': LIGHT_THEME,
            'dark': DARK_THEME,
        }
    
    def get_theme(self, theme_name: str = 'light') -> ThemeColors:
        """
        Vraća temu po imenu.
        
        Args:
            theme_name: Ime teme ('light' ili 'dark')
        
        Returns:
            ThemeColors objekat
        """
        return self.themes.get(theme_name, LIGHT_THEME)
    
    def get_all_themes(self) -> Dict[str, Dict[str, str]]:
        """
        Vraća sve dostupne teme.
        
        Returns:
            Dict svih tema
        """
        return {
            'light': {
                'primary': LIGHT_THEME.primary,
                'background': LIGHT_THEME.background,
                'surface': LIGHT_THEME.surface,
                'text': LIGHT_THEME.text,
                'border': LIGHT_THEME.border,
            },
            'dark': {
                'primary': DARK_THEME.primary,
                'background': DARK_THEME.background,
                'surface': DARK_THEME.surface,
                'text': DARK_THEME.text,
                'border': DARK_THEME.border,
            }
        }
    
    def get_css_variables(self, theme_name: str = 'light') -> str:
        """
        Generiše CSS variables za temu.
        
        Args:
            theme_name: Ime teme
        
        Returns:
            CSS string sa variables
        """
        theme = self.get_theme(theme_name)
        
        return f"""
        :root {{
            --color-primary: {theme.primary};
            --color-primary-hover: {theme.primary_hover};
            --color-secondary: {theme.secondary};
            --color-background: {theme.background};
            --color-surface: {theme.surface};
            --color-text: {theme.text};
            --color-text-secondary: {theme.text_secondary};
            --color-border: {theme.border};
            --color-success: {theme.success};
            --color-warning: {theme.warning};
            --color-error: {theme.error};
            --color-info: {theme.info};
        }}
        """
    
    def toggle_theme(self, current_theme: str) -> str:
        """
        Prebacuje između light i dark teme.
        
        Args:
            current_theme: Trenutna tema
        
        Returns:
            Nova tema
        """
        if current_theme == 'light':
            return 'dark'
        return 'light'
    
    def is_valid_theme(self, theme_name: str) -> bool:
        """
        Proverava da li je tema validna.
        
        Args:
            theme_name: Ime teme
        
        Returns:
            True ako je tema validna
        """
        return theme_name in self.themes


theme_service = ThemeService()
