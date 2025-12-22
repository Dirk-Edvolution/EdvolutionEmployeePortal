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
    - chile: Chile (national calendar)
    - colombia: Colombia (national calendar - includes Bogotá)
    """

    # Year-specific holidays (most accurate)
    # Format: {region: {year: [(date_str, name, note), ...]}}
    YEAR_SPECIFIC_HOLIDAYS = {
        'mexico': {
            2024: [
                ('2024-01-01', 'Año Nuevo', None),
                ('2024-02-05', 'Día de la Constitución', None),
                ('2024-03-18', 'Natalicio de Benito Juárez', 'Feriado puente'),
                ('2024-05-01', 'Día del Trabajo', None),
                ('2024-09-16', 'Día de la Independencia Mexicana', None),
                ('2024-11-18', 'Día de la Revolución Mexicana', 'Feriado puente'),
                ('2024-12-25', 'Navidad', None),
            ],
            2025: [
                ('2025-01-01', 'Año Nuevo', None),
                ('2025-02-03', 'Día de la Constitución', 'Feriado puente. El festivo del 5 de febrero se traslada al lunes 3'),
                ('2025-03-17', 'Natalicio de Benito Juárez', 'Feriado puente. El festivo del 21 de marzo se traslada al lunes 17'),
                ('2025-05-01', 'Día del Trabajo', None),
                ('2025-09-16', 'Día de la Independencia Mexicana', None),
                ('2025-11-17', 'Día de la Revolución Mexicana', 'Feriado puente. El festivo del 20 de noviembre se traslada al lunes 17'),
                ('2025-12-25', 'Navidad', None),
            ],
            2026: [
                ('2026-01-01', 'Año Nuevo', None),
                ('2026-02-02', 'Día de la Constitución', 'Feriado puente. El festivo del 5 de febrero se traslada al lunes 2'),
                ('2026-03-16', 'Natalicio de Benito Juárez', 'Feriado puente. El festivo del 21 de marzo se traslada al lunes 16'),
                ('2026-05-01', 'Día del Trabajo', 'Feriado puente'),
                ('2026-09-16', 'Día de la Independencia Mexicana', None),
                ('2026-11-16', 'Día de la Revolución Mexicana', 'Feriado puente. El festivo del 20 de noviembre se traslada al lunes 16'),
                ('2026-12-25', 'Navidad', 'Feriado puente'),
            ]
        },
        'madrid': {
            2026: [
                ('2026-01-01', 'Año Nuevo', None),
                ('2026-01-06', 'Epifanía del Señor', None),
                ('2026-04-02', 'Jueves Santo', None),
                ('2026-04-03', 'Viernes Santo', None),
                ('2026-05-01', 'Fiesta del Trabajo', None),
                ('2026-05-02', 'Fiesta de la Comunidad de Madrid', None),
                ('2026-08-15', 'Asunción de la Virgen', None),
                ('2026-10-12', 'Fiesta Nacional de España', None),
                ('2026-11-02', 'Traslado de Todos los Santos', None),
                ('2026-12-07', 'Traslado del Día de la Constitución Española', None),
                ('2026-12-08', 'Día de la Inmaculada Concepción', None),
                ('2026-12-25', 'Natividad del Señor', None),
            ]
        },
        'andalucia': {
            2026: [
                ('2026-01-01', 'Año Nuevo', None),
                ('2026-01-06', 'Epifanía del Señor', None),
                ('2026-02-28', 'Día de Andalucía', None),
                ('2026-04-02', 'Jueves Santo', None),
                ('2026-04-03', 'Viernes Santo', None),
                ('2026-04-22', 'Miércoles de Feria', None),
                ('2026-05-01', 'Fiesta del Trabajo', None),
                ('2026-06-04', 'Fiesta del Corpus Cristi', None),
                ('2026-08-15', 'Asunción de la Virgen', None),
                ('2026-10-12', 'Fiesta Nacional de España', None),
                ('2026-11-02', 'Festividad de todos los santos (Traslado)', None),
                ('2026-12-07', 'Día de la Constitución (Traslado)', None),
                ('2026-12-08', 'La Inmaculada Concepción', None),
                ('2026-12-25', 'Natividad del Señor', None),
            ]
        },
        'colombia': {
            2026: [
                ('2026-01-01', 'Año Nuevo', None),
                ('2026-01-12', 'Reyes Magos', None),
                ('2026-03-23', 'Día de San José', None),
                ('2026-04-02', 'Jueves Santo', None),
                ('2026-04-03', 'Viernes Santo', None),
                ('2026-05-01', 'Día del trabajo', None),
                ('2026-05-18', 'Ascensión de Jesús', None),
                ('2026-06-08', 'Corpus Christi', None),
                ('2026-06-15', 'Sagrado Corazón de Jesús', None),
                ('2026-06-29', 'San Pedro y San Pablo', None),
                ('2026-07-20', 'Día de la independencia', None),
                ('2026-08-07', 'Batalla de Boyacá', None),
                ('2026-08-17', 'Asunción de la Virgen', None),
                ('2026-10-12', 'Día de la raza', None),
                ('2026-11-02', 'Todos los Santos', None),
                ('2026-11-16', 'Independencia de Cartagena', None),
                ('2026-12-08', 'Inmaculada Concepción', None),
                ('2026-12-25', 'Navidad', None),
            ]
        },
        'chile': {
            2026: [
                ('2026-01-01', 'Año Nuevo', 'Irrenunciable'),
                ('2026-04-03', 'Viernes Santo', 'Religioso'),
                ('2026-04-04', 'Sábado Santo', 'Religioso'),
                ('2026-05-01', 'Día Nacional del Trabajo', 'Irrenunciable'),
                ('2026-05-21', 'Día de las Glorias Navales', None),
                ('2026-06-21', 'Día Nacional de los Pueblos Indígenas', None),
                ('2026-06-29', 'San Pedro y San Pablo', 'Religioso'),
                ('2026-07-16', 'Día de la Virgen del Carmen', 'Religioso'),
                ('2026-08-15', 'Asunción de la Virgen', 'Religioso'),
                ('2026-09-18', 'Independencia Nacional', 'Irrenunciable'),
                ('2026-09-19', 'Día de las Glorias del Ejército', 'Irrenunciable'),
                ('2026-10-12', 'Encuentro de Dos Mundos', None),
                ('2026-10-31', 'Día de las Iglesias Evangélicas y Protestantes', 'Religioso'),
                ('2026-11-01', 'Día de Todos los Santos', 'Religioso'),
                ('2026-12-08', 'Inmaculada Concepción', 'Religioso'),
                ('2026-12-25', 'Navidad', 'Irrenunciable'),
            ]
        },
        # Aliases for consistency
        'bogota': {  # Colombia national calendar applies
            2026: [
                ('2026-01-01', 'Año Nuevo', None),
                ('2026-01-12', 'Reyes Magos', None),
                ('2026-03-23', 'Día de San José', None),
                ('2026-04-02', 'Jueves Santo', None),
                ('2026-04-03', 'Viernes Santo', None),
                ('2026-05-01', 'Día del trabajo', None),
                ('2026-05-18', 'Ascensión de Jesús', None),
                ('2026-06-08', 'Corpus Christi', None),
                ('2026-06-15', 'Sagrado Corazón de Jesús', None),
                ('2026-06-29', 'San Pedro y San Pablo', None),
                ('2026-07-20', 'Día de la independencia', None),
                ('2026-08-07', 'Batalla de Boyacá', None),
                ('2026-08-17', 'Asunción de la Virgen', None),
                ('2026-10-12', 'Día de la raza', None),
                ('2026-11-02', 'Todos los Santos', None),
                ('2026-11-16', 'Independencia de Cartagena', None),
                ('2026-12-08', 'Inmaculada Concepción', None),
                ('2026-12-25', 'Navidad', None),
            ]
        },
        'santiago_chile': {  # Alias for Chile
            2026: [
                ('2026-01-01', 'Año Nuevo', 'Irrenunciable'),
                ('2026-04-03', 'Viernes Santo', 'Religioso'),
                ('2026-04-04', 'Sábado Santo', 'Religioso'),
                ('2026-05-01', 'Día Nacional del Trabajo', 'Irrenunciable'),
                ('2026-05-21', 'Día de las Glorias Navales', None),
                ('2026-06-21', 'Día Nacional de los Pueblos Indígenas', None),
                ('2026-06-29', 'San Pedro y San Pablo', 'Religioso'),
                ('2026-07-16', 'Día de la Virgen del Carmen', 'Religioso'),
                ('2026-08-15', 'Asunción de la Virgen', 'Religioso'),
                ('2026-09-18', 'Independencia Nacional', 'Irrenunciable'),
                ('2026-09-19', 'Día de las Glorias del Ejército', 'Irrenunciable'),
                ('2026-10-12', 'Encuentro de Dos Mundos', None),
                ('2026-10-31', 'Día de las Iglesias Evangélicas y Protestantes', 'Religioso'),
                ('2026-11-01', 'Día de Todos los Santos', 'Religioso'),
                ('2026-12-08', 'Inmaculada Concepción', 'Religioso'),
                ('2026-12-25', 'Navidad', 'Irrenunciable'),
            ]
        },
    }

    # Fallback: Regional holiday calendars (format: (month, day, name))
    # Used for years not in YEAR_SPECIFIC_HOLIDAYS
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
        # First, check if we have year-specific holiday data
        if region in cls.YEAR_SPECIFIC_HOLIDAYS:
            year_data = cls.YEAR_SPECIFIC_HOLIDAYS[region].get(date_obj.year)
            if year_data:
                # Check against specific dates for this year
                date_str = date_obj.isoformat()
                for holiday_date_str, name, note in year_data:
                    if holiday_date_str == date_str:
                        logger.debug(f"Date {date_obj} is holiday: {name} in {region}")
                        return True
                # Year data exists but date not found - not a holiday
                return False

        # Fall back to pattern-based REGIONAL_HOLIDAYS for years without specific data
        if region not in cls.REGIONAL_HOLIDAYS:
            logger.warning(f"Unknown holiday region: {region}, defaulting to no holidays")
            return False

        # Check fixed holidays by month/day pattern
        for month, day, name in cls.REGIONAL_HOLIDAYS[region]:
            if date_obj.month == month and date_obj.day == day:
                logger.debug(f"Date {date_obj} is holiday: {name} in {region}")
                return True

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
        holidays = []
        current_date = start_date

        # Collect all years in the range
        years = set()
        temp_date = start_date
        while temp_date <= end_date:
            years.add(temp_date.year)
            temp_date += timedelta(days=365)

        # Check if we have year-specific data for any year in range
        has_year_specific = region in cls.YEAR_SPECIFIC_HOLIDAYS

        if has_year_specific:
            # Use year-specific data
            for year in years:
                year_data = cls.YEAR_SPECIFIC_HOLIDAYS[region].get(year)
                if year_data:
                    for holiday_date_str, name, note in year_data:
                        holiday_date = date.fromisoformat(holiday_date_str)
                        if start_date <= holiday_date <= end_date:
                            holidays.append({
                                'date': holiday_date,
                                'name': name,
                                'note': note,
                                'is_weekend': cls.is_weekend(holiday_date)
                            })

        # Fall back to pattern-based if no year-specific data
        if not has_year_specific and region in cls.REGIONAL_HOLIDAYS:
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

        # Sort by date
        holidays.sort(key=lambda x: x['date'])
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
        holidays = []

        # First, check if we have year-specific data
        if region in cls.YEAR_SPECIFIC_HOLIDAYS:
            year_data = cls.YEAR_SPECIFIC_HOLIDAYS[region].get(year)
            if year_data:
                # Use year-specific data
                for holiday_date_str, name, note in year_data:
                    holiday_date = date.fromisoformat(holiday_date_str)
                    holidays.append({
                        'date': holiday_date,
                        'name': name,
                        'note': note,
                        'is_weekend': cls.is_weekend(holiday_date)
                    })
                # Sort by date and return
                holidays.sort(key=lambda x: x['date'])
                return holidays

        # Fall back to pattern-based REGIONAL_HOLIDAYS
        if region not in cls.REGIONAL_HOLIDAYS:
            return []

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
