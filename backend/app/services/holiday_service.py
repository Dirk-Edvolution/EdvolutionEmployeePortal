"""
Regional Holiday Calendar Service

Manages regional public holidays for accurate time-off calculations.
Excludes weekends (Saturday/Sunday) and region-specific non-working days.
"""
from datetime import datetime, timedelta, date
from typing import List, Dict, Set, Optional
import logging

logger = logging.getLogger(__name__)


class HolidayService:
    """
    Service for managing regional holiday calendars

    Regions supported:
    - madrid: Madrid, Spain
    - andalucia: Andalucía, Spain
    - mexico: Mexico (national calendar)
    - santiago_chile: Santiago, Chile
    - caracas: Caracas, Venezuela
    - bogota: Bogotá, Colombia
    """

    # Regional holiday calendars (format: (month, day, name))
    # Note: These are fixed holidays. For movable holidays (Easter, etc.),
    # they should be calculated dynamically or added per year

    REGIONAL_HOLIDAYS = {
        'madrid': [
            # National Spanish holidays
            (1, 1, 'Año Nuevo'),
            (1, 6, 'Epifanía del Señor / Día de Reyes'),
            (5, 1, 'Fiesta del Trabajo'),
            (8, 15, 'Asunción de la Virgen'),
            (10, 12, 'Fiesta Nacional de España'),
            (11, 1, 'Todos los Santos'),
            (12, 6, 'Día de la Constitución'),
            (12, 8, 'Inmaculada Concepción'),
            (12, 25, 'Navidad'),
            # Madrid regional holidays
            (5, 2, 'Fiesta de la Comunidad de Madrid'),
            (5, 15, 'San Isidro (Patrón de Madrid)'),
            # Note: Add Jueves Santo, Viernes Santo (variable dates)
        ],

        'andalucia': [
            # National Spanish holidays
            (1, 1, 'Año Nuevo'),
            (1, 6, 'Epifanía del Señor / Día de Reyes'),
            (5, 1, 'Fiesta del Trabajo'),
            (8, 15, 'Asunción de la Virgen'),
            (10, 12, 'Fiesta Nacional de España'),
            (11, 1, 'Todos los Santos'),
            (12, 6, 'Día de la Constitución'),
            (12, 8, 'Inmaculada Concepción'),
            (12, 25, 'Navidad'),
            # Andalucía regional holidays
            (2, 28, 'Día de Andalucía'),
            # Note: Add Jueves Santo, Viernes Santo (variable dates)
        ],

        'mexico': [
            (1, 1, 'Año Nuevo'),
            (2, 5, 'Día de la Constitución'),  # First Monday of February
            (3, 21, 'Natalicio de Benito Juárez'),  # Third Monday of March
            (5, 1, 'Día del Trabajo'),
            (9, 16, 'Día de la Independencia'),
            (11, 20, 'Día de la Revolución'),  # Third Monday of November
            (12, 25, 'Navidad'),
            # Note: Some are moved to Mondays by law
        ],

        'santiago_chile': [
            (1, 1, 'Año Nuevo'),
            (5, 1, 'Día del Trabajo'),
            (5, 21, 'Día de las Glorias Navales'),
            (6, 29, 'San Pedro y San Pablo'),  # Can be moved to nearest Monday
            (7, 16, 'Día de la Virgen del Carmen'),
            (8, 15, 'Asunción de la Virgen'),
            (9, 18, 'Primera Junta Nacional de Gobierno'),
            (9, 19, 'Día de las Glorias del Ejército'),
            (10, 12, 'Encuentro de Dos Mundos'),  # Can be moved to nearest Monday
            (11, 1, 'Día de Todos los Santos'),
            (12, 8, 'Inmaculada Concepción'),
            (12, 25, 'Navidad'),
            # Note: Add Viernes Santo, Sábado Santo (variable dates)
        ],

        'caracas': [
            (1, 1, 'Año Nuevo'),
            (2, 19, 'Día de la Federación'),  # Monday/Tuesday of Carnival
            (2, 20, 'Carnaval'),  # Monday/Tuesday of Carnival
            (3, 19, 'Día de San José'),
            (4, 19, 'Declaración de la Independencia'),
            (5, 1, 'Día del Trabajador'),
            (6, 24, 'Batalla de Carabobo'),
            (7, 5, 'Día de la Independencia'),
            (7, 24, 'Natalicio del Libertador Simón Bolívar'),
            (10, 12, 'Día de la Resistencia Indígena'),
            (12, 24, 'Nochebuena'),
            (12, 25, 'Navidad'),
            (12, 31, 'Fin de Año'),
            # Note: Add Jueves Santo, Viernes Santo (variable dates)
        ],

        'bogota': [
            (1, 1, 'Año Nuevo'),
            (1, 8, 'Día de los Reyes Magos'),  # Moved to next Monday
            (3, 19, 'Día de San José'),  # Moved to next Monday
            (5, 1, 'Día del Trabajo'),
            (5, 29, 'Ascensión del Señor'),  # Moved to next Monday (39 days after Easter)
            (6, 19, 'Corpus Christi'),  # Moved to next Monday (60 days after Easter)
            (6, 26, 'Sagrado Corazón de Jesús'),  # Moved to next Monday
            (7, 20, 'Día de la Independencia'),
            (8, 7, 'Batalla de Boyacá'),
            (8, 20, 'Asunción de la Virgen'),  # Moved to next Monday
            (10, 15, 'Día de la Raza'),  # Moved to next Monday
            (11, 5, 'Día de Todos los Santos'),  # Moved to next Monday
            (11, 12, 'Independencia de Cartagena'),  # Moved to next Monday
            (12, 8, 'Inmaculada Concepción'),
            (12, 25, 'Navidad'),
            # Note: Add Jueves Santo, Viernes Santo (variable dates)
        ],
    }

    @classmethod
    def get_available_regions(cls) -> List[Dict[str, str]]:
        """Get list of available holiday regions"""
        return [
            {'code': 'madrid', 'name': 'Madrid, España'},
            {'code': 'andalucia', 'name': 'Andalucía, España'},
            {'code': 'mexico', 'name': 'México'},
            {'code': 'santiago_chile', 'name': 'Santiago de Chile, Chile'},
            {'code': 'caracas', 'name': 'Caracas, Venezuela'},
            {'code': 'bogota', 'name': 'Bogotá, Colombia'},
        ]

    @classmethod
    def is_weekend(cls, date_obj: date) -> bool:
        """Check if a date is a weekend (Saturday or Sunday)"""
        return date_obj.weekday() in [5, 6]  # 5=Saturday, 6=Sunday

    @classmethod
    def is_public_holiday(cls, date_obj: date, region: str) -> bool:
        """
        Check if a date is a public holiday in the given region

        Args:
            date_obj: Date to check
            region: Holiday region code

        Returns:
            True if the date is a public holiday
        """
        if region not in cls.REGIONAL_HOLIDAYS:
            logger.warning(f"Unknown holiday region: {region}, defaulting to no holidays")
            return False

        # Check fixed holidays
        for month, day, name in cls.REGIONAL_HOLIDAYS[region]:
            if date_obj.month == month and date_obj.day == day:
                logger.debug(f"Date {date_obj} is holiday: {name} in {region}")
                return True

        # TODO: Add movable holiday calculation (Easter-based holidays, etc.)

        return False

    @classmethod
    def is_working_day(cls, date_obj: date, region: Optional[str] = None) -> bool:
        """
        Check if a date is a working day (not weekend, not holiday)

        Args:
            date_obj: Date to check
            region: Holiday region code (if None, only checks weekends)

        Returns:
            True if the date is a working day
        """
        if cls.is_weekend(date_obj):
            return False

        if region and cls.is_public_holiday(date_obj, region):
            return False

        return True

    @classmethod
    def count_working_days(
        cls,
        start_date: date,
        end_date: date,
        region: Optional[str] = None
    ) -> int:
        """
        Count working days between two dates (inclusive)
        Excludes weekends and regional public holidays

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            region: Holiday region code (if None, only excludes weekends)

        Returns:
            Number of working days
        """
        if start_date > end_date:
            return 0

        working_days = 0
        current_date = start_date

        while current_date <= end_date:
            if cls.is_working_day(current_date, region):
                working_days += 1
            current_date += timedelta(days=1)

        logger.info(
            f"Counted {working_days} working days between {start_date} and {end_date} "
            f"(region: {region or 'none'})"
        )

        return working_days

    @classmethod
    def get_holidays_in_range(
        cls,
        start_date: date,
        end_date: date,
        region: str
    ) -> List[Dict[str, any]]:
        """
        Get list of holidays within a date range

        Args:
            start_date: Start date
            end_date: End date
            region: Holiday region code

        Returns:
            List of holiday dictionaries with date and name
        """
        if region not in cls.REGIONAL_HOLIDAYS:
            return []

        holidays = []
        current_date = start_date

        while current_date <= end_date:
            for month, day, name in cls.REGIONAL_HOLIDAYS[region]:
                if current_date.month == month and current_date.day == day:
                    holidays.append({
                        'date': current_date,
                        'name': name,
                        'is_weekend': cls.is_weekend(current_date)
                    })
            current_date += timedelta(days=1)

        return holidays

    @classmethod
    def get_year_holidays(cls, year: int, region: str) -> List[Dict[str, any]]:
        """
        Get all holidays for a specific year and region

        Args:
            year: Year to get holidays for
            region: Holiday region code

        Returns:
            List of holiday dictionaries with date and name
        """
        if region not in cls.REGIONAL_HOLIDAYS:
            return []

        holidays = []
        for month, day, name in cls.REGIONAL_HOLIDAYS[region]:
            try:
                holiday_date = date(year, month, day)
                holidays.append({
                    'date': holiday_date,
                    'name': name,
                    'is_weekend': cls.is_weekend(holiday_date)
                })
            except ValueError:
                # Invalid date (e.g., Feb 29 in non-leap year)
                continue

        # Sort by date
        holidays.sort(key=lambda x: x['date'])

        return holidays
