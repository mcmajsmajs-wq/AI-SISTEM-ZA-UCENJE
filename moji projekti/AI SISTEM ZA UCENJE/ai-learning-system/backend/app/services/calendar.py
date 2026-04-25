# -*- coding: utf-8 -*-
"""
===============================================================================
CALENDAR SERVICE - Spaced Repetition
===============================================================================
Servis za kalendar i sistem ponavljanja (Spaced Repetition).

Verzija: 1.0.0
===============================================================================
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger(__name__)


SPACED_REPETITION_INTERVALS = {
    1: 1,
    2: 3,
    3: 7,
    4: 14,
    5: 30,
    6: 60,
    7: 120,
}


@dataclass
class StudySession:
    """Podaci o studijskoj sesiji."""
    id: int
    user_id: int
    document_id: int
    quiz_id: Optional[int]
    scheduled_at: datetime
    completed_at: Optional[datetime]
    status: str
    notes: str = ""


@dataclass
class ReviewItem:
    """Stavka za ponavljanje."""
    item_type: str
    item_id: int
    title: str
    next_review: datetime
    ease_factor: float
    interval: int
    repetitions: int
    due_today: bool


class CalendarService:
    """
    ================================================================================
    CALENDAR SERVICE
    ================================================================================
    Servis za upravljanje kalendarom i sistemom ponavljanja.
    ================================================================================
    """
    
    def calculate_next_review(
        self,
        quality: int,
        ease_factor: float,
        interval: int,
        repetitions: int
    ) -> tuple[float, int, int]:
        """
        Računa sledeći interval ponavljanja na osnovu SM-2 algoritma.
        
        Args:
            quality: Kvalitet odgovora (0-5)
            ease_factor: Faktor olakšanja
            interval: Trenutni interval
            repetitions: Broj ponavljanja
        
        Returns:
            (new_ease_factor, new_interval, new_repetitions)
        """
        if quality < 3:
            repetitions = 0
            interval = 1
        else:
            if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 3
            else:
                interval = int(interval * ease_factor)
            
            repetitions += 1
        
        ease_factor = max(1.3, ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
        
        return ease_factor, interval, repetitions
    
    def get_due_items(
        self,
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Vraća stavke koje su danas za ponavljanje.
        
        Args:
            items: Lista stavki sa next_review datumom
        
        Returns:
            Lista stavki koje treba ponoviti danas
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        due_items = [
            item for item in items
            if datetime.fromisoformat(str(item.get('next_review', ''))) <= today
        ]
        
        return sorted(due_items, key=lambda x: x.get('next_review', ''))
    
    def generate_study_schedule(
        self,
        document_title: str,
        num_sessions: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Generiše raspored učenja za dokument.
        
        Args:
            document_title: Naslov dokumenta
            num_sessions: Broj sesija
        
        Returns:
            Lista sesija sa datumima
        """
        sessions = []
        base_date = datetime.now()
        
        for i in range(num_sessions):
            session_date = base_date + timedelta(days=i * 2)
            
            sessions.append({
                'date': session_date.isoformat(),
                'day_name': session_date.strftime('%A'),
                'day_number': session_date.day,
                'topics': [f"Deo {i+1}: {document_title}"],
                'duration_minutes': 15 + (i * 5),
            })
        
        return sessions
    
    def get_weekly_availability(
        self,
        user_id: int,
        start_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Vraća nedeljnu dostupnost za učenje.
        
        Args:
            user_id: ID korisnika
            start_date: Početni datum
        
        Returns:
            Nedeljni kalendar
        """
        if start_date is None:
            start_date = datetime.now()
        
        week_days = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            
            day_info = {
                'date': day.isoformat(),
                'day_name': day.strftime('%A'),
                'day_number': day.day,
                'month': day.strftime('%B'),
                'is_today': day.date() == datetime.now().date(),
                'available_slots': self._calculate_available_slots(day),
                'sessions': [],
            }
            
            week_days.append(day_info)
        
        return {
            'week_start': start_date.isoformat(),
            'week_end': (start_date + timedelta(days=6)).isoformat(),
            'days': week_days,
        }
    
    def _calculate_available_slots(self, date: datetime) -> List[Dict[str, Any]]:
        """Računa dostupne slotove za datum."""
        slots = []
        
        study_hours = [9, 10, 11, 14, 15, 16, 17, 18, 19, 20]
        
        for hour in study_hours:
            slot_time = date.replace(hour=hour, minute=0)
            
            if slot_time > datetime.now():
                slots.append({
                    'time': f"{hour}:00",
                    'available': True,
                })
        
        return slots
    
    def calculate_streak(
        self,
        study_sessions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Računa trenutnu seriju uzastopnih dana učenja.
        
        Args:
            study_sessions: Lista završenih sesija
        
        Returns:
            Informacije o seriji
        """
        if not study_sessions:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'total_days': 0,
            }
        
        dates = sorted(set(
            datetime.fromisoformat(str(s['completed_at'])).date()
            for s in study_sessions
            if s.get('completed_at')
        ))
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 1
        
        today = datetime.now().date()
        
        for i, date in enumerate(dates):
            if i > 0:
                if (date - dates[i-1]).days == 1:
                    temp_streak += 1
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
            
            if date >= today - timedelta(days=1):
                current_streak = temp_streak
        
        longest_streak = max(longest_streak, temp_streak)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'total_days': len(dates),
        }


calendar_service = CalendarService()
