import datetime
from course import Course
from config import *
import icalendar

class SchoolParser:
    def __init__(self):
        self.courses = []
    
    def set_header(self, header):
        self.header = header

    # 3-18周 / 星期三 / 5-6节
    # 4-18周双周 / 星期五 / 5
    # 1-2周         -> ERROR
    # 第2周;第3周   -> ERROR
    def curriculum_parser(self, time_str, note=""):
        time = [part.strip() for part in time_str.split("/")]

        if len(time) != 3:
            # fallback if encounter unknown format (probably not arranged)
            return self.curriculum_parser(fallback_time, note="err_time")
        
        (weeks_part, weekday_part, sections_part) = tuple(time)
        
        try:
            # Parse weeks
            weeks = []
            if "双周" in weeks_part:
                start_week, end_week = map(int, weeks_part.replace("双周", "").replace("周", "").strip().split("-"))
                weeks = [week for week in range(start_week, end_week + 1) if week % 2 == 0]
            elif "单周" in weeks_part:
                start_week, end_week = map(int, weeks_part.replace("单周", "").replace("周", "").strip().split("-"))
                weeks = [week for week in range(start_week, end_week + 1) if week % 2 == 1]
            else:
                week_str = weeks_part.replace("周", "").strip()
                if "-" in week_str:
                    start_week, end_week = map(int, week_str.split("-"))
                    weeks = list(range(start_week, end_week + 1))
                else:
                    week = int(week_str)
                    weeks = [week]
        except Exception as e:
            # raise ValueError(f"Error parsing weeks part: {weeks_part}") from e
            return self.curriculum_parser(fallback_time, note="err_time")
        
        # Parse weekday
        weekday_map = {
            "星期一": 1,
            "星期二": 2,
            "星期三": 3,
            "星期四": 4,
            "星期五": 5,
            "星期六": 6,
            "星期日": 7
        }
        weekday = weekday_map.get(weekday_part.strip(), 0)
        
        # Parse sections
        sections = []
        if "-" in sections_part:
            start_section, end_section = map(int, sections_part.replace("节", "").strip().split("-"))
            sections = list(range(start_section, end_section + 1))
        else:
            sections = [int(sections_part.replace("节", "").strip())]
        
        return weeks, weekday, sections, note

    def course_parser(self, course_id, name, teacher, time_str, location, description=""):
        weeks, weekday, sections, note = self.curriculum_parser(time_str)
        
        if "err_time" in note:
            description = "**MAYBE UNARRANGED COURSE**" + description

        if not name:
            name = fallback_name
        if not teacher:
            teacher = fallback_teacher
        if not location:
            location = fallback_location

        course = Course(courseid=course_id, name=name, teacher=teacher, location=location, weeks=weeks, weekday=weekday, sections=sections, description=description)
        self.courses.append(course)
        return course
    
    def col_parser(self,col):
        #['203170020', '大学化学（Ⅴ）', '日历\n\n李建梅（无）', '大纲\n\n中文大纲\n\n英文大纲', '04', '2', '必修', '', '', '李建梅*', '正常', '置入', '', '', '', '3-18周 / 星期三 / 5-6节', '江安 / 一教B座 / B104']

        describtion = ""
        col_to_description_index = [16,15,9,0,1]
        for index in col_to_description_index:
                try:
                    describtion += f"{self.header[index]}: {col[index]}\n"
                except Exception as e:
                    describtion += f"{self.header[index]}: err_col: {e}\n"

        return self.course_parser(course_id=col[0], name=col[1], teacher=col[9], time_str=col[15], location=col[16],description=describtion)
    
    def generate_ics(self):
        cal = icalendar.Calendar()
        cal.add('prodid', '-//Schedule Parser//mxgmn//')
        cal.add('version', '2.0')
        
        for course in self.courses:
            events = course.course_to_events()
            for event in events:
                cal.add_component(event)

        file = open(f"schedule-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.ics", "wb")
        file.write(cal.to_ical())
        file.close()