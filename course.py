import icalendar
import datetime
from config import *

class Course:
    def __init__(self, courseid: str, name: str, teacher: str, location: str, weeks: list[int], weekday: int, sections: list[int], description: str=""):
        self.courseid = courseid
        self.name = name
        self.teacher = teacher
        self.location = location
        self.weeks = weeks
        self.weekday = weekday
        self.sections = sections
        self.description = description
        self.first_week = datetime.date.fromisoformat(first_week_day).isocalendar()[1]

    def get_date_of_week(self, week: int):
        first_date = datetime.date.fromisoformat(first_week_day)
        year = first_date.year
        week_num = self.first_week + week - 1
        # 计算该年第 week_num 周的第一天，如果溢出则自动到下一年
        try:
            date = datetime.date.fromisocalendar(year, week_num, self.weekday)
        except ValueError:
            # 溢出到下一年
            year += 1
            week_num = week_num - datetime.date(year - 1, 12, 28).isocalendar()[1]
            date = datetime.date.fromisocalendar(year, week_num, self.weekday)
        return date
        #return datetime.date.fromisocalendar(year, self.first_week + week - 1, self.weekday)


    def get_section_period(self):
        campus = self.location.split(" / ")[0]
        time_table = time_table_huaxi
        if campus == "江安":
            time_table = time_table_jiangan
        
        return (time_table[self.sections[0]][0], time_table[self.sections[-1]][1])

    def course_to_events(self):
        events = []
        for week in self.weeks:
            # we know week and weekday, so we can calculate the date
            date = self.get_date_of_week(week)
            event = icalendar.Event()
            event.add('summary', self.name)
            event.add('location', self.location)
            event.add('description', self.description)
            tzinfo = datetime.timezone(datetime.timedelta(hours=time_zone))
            event.add('dtstart', datetime.datetime.combine(date, datetime.datetime.strptime(self.get_section_period()[0], "%H:%M").time(), tzinfo=tzinfo))
            event.add('dtend', datetime.datetime.combine(date, datetime.datetime.strptime(self.get_section_period()[1], "%H:%M").time(), tzinfo=tzinfo))
            events.append(event)
            
        return events
