import asyncio
from datetime import datetime
from sys_msg import system_message

class SafeGuards:
    def __init__(self, companies_list: list, pickup_datetime: datetime, dropoff_datetime: datetime):
        self.companies_list = companies_list
        self.pickup_datetime = pickup_datetime
        self.dropoff_datetime = dropoff_datetime
    
    async def _validate_time(self, time_datetime: datetime, label: str, company: str):
        print(f"{system_message('I')} Validating {label} Time for {company}")
        
        # Validate time format HH:MM with allowed values.
        try:
            hour = time_datetime.hour
            minute = time_datetime.minute
        except ValueError:
            raise ValueError(f"{label}: Invalid format '{time_datetime}'. Expected HH:MM.")

        # Validate Time
        allowed_minutes = [00, 15, 30, 45]
        current_datetime = datetime.now()
        if (time_datetime.time() < current_datetime.time() and time_datetime.date() == current_datetime.date()):
            for cur_minute in allowed_minutes:
                if (cur_minute > current_datetime.minute):
                    raise ValueError(f"{label}: Invalid time {time_datetime.hour}:{time_datetime.minute}. Time must at least be {current_datetime.hour}:{cur_minute}")
                    break
                
        print(f"{system_message('S')} Valid {label} Time")

        # Validate Hour
        if not (isinstance(hour, (int))) or not (0 <= int(hour) <= 23):
            raise ValueError(f"{label}: Invalid hour '{hour}'. Must be between 00 and 23.")

        # Validate Minute
        if minute not in allowed_minutes:
            raise ValueError(f"{label}: Invalid minute '{minute}'. Must be one of {sorted(allowed_minutes)}.")
        
    async def _validate_date(self, time_datetime: datetime, label: str, company: str):
        print(f"{system_message('I')} Validating {label} Date for {company}")
        
        # Validate time format HH:MM with allowed values.
        try:
            day = time_datetime.day
            month = time_datetime.month
            year = time_datetime.year
        except ValueError:
            raise ValueError(f"{label}: Invalid format '{time_datetime}'. Expected DD/MM/YYYY.")
        
        # Validate Day
        current_datetime = datetime.now()
        today = current_datetime.date()
        if (time_datetime.date() < today):
            raise ValueError(f"{label}: Invalid date '{day}/{month}/{year}'. Date must be greater or equal to {today.day}/{today.month}/{today.year}")
        
        print(f"{system_message('S')} Valid {label} Date")
        
    async def safeguard(self):
        for company in self.companies_list:
            # Validate Hertz
            if (company == "Hertz"):
                # Validate Time
                await self._validate_time(self.pickup_datetime, "Pick-Up", company)
                await self._validate_time(self.dropoff_datetime, "Drop-Off", company)
                
                # # Validate Date
                await self._validate_date(self.pickup_datetime, "Pick-Up", company)
                await self._validate_date(self.dropoff_datetime, "Drop-Off", company)