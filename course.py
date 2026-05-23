import icalendar
import datetime
from config import *

class Course:
    def __init__(self, course:dict):
        self.no_schedule = len(course.get('timeAndPlaceList', [])) == 0
        
        if self.no_schedule:
            tmp_tapl = {
                'coureNumber': course.get('coureNumber', course['id']['coureNumber']),
                'coureSequenceNumber': course.get('coureSequenceNumber', course['id']['coureSequenceNumber']),
                'coureName': course.get('coureName', course.get('courseName', fallback_name)),
                'coursePropertiesName': course.get('coursePropertiesName', '必修'),
                'campusName': '',
                'teachingBuildingName': '',
                'classroomName': fallback_location,
                'classWeek': '1' + '0' * 24,
                'classDay': 7,
                'classSessions': 1,
                'continuingSession': 12,
                'weekDescription': '1周',
            }
        else:
            tmp_tapl = course['timeAndPlaceList'][0]
        
        self.courseid = tmp_tapl['coureNumber'] + "_" + tmp_tapl['coureSequenceNumber']
        self.name = tmp_tapl['coureName']
        self.teacher = course['attendClassTeacher']

        self.location = (tmp_tapl['campusName'], tmp_tapl['teachingBuildingName'], tmp_tapl['classroomName'])
        # 111111111111000000000000 处理二进制的周数表示，转换成整数列表
        tmp_weeks = []
        for i in range(len(tmp_tapl['classWeek'])):
            if tmp_tapl['classWeek'][i] == '1':
                tmp_weeks.append(i + 1)
        self.weeks = tmp_weeks
        self.weekday = tmp_tapl['classDay']
        # 处理节数 sessions 5, continuingSession 3，表示从第5节开始连续上3节，即5,6,7节
        tmp_sections = []
        for i in range(tmp_tapl['continuingSession']):
            tmp_sections.append(tmp_tapl['classSessions'] + i)
        self.sections = tmp_sections
        
        # 生成description，包含各种信息
        desc = []
        if self.no_schedule:
            desc.append("（本课程没有安排时间）")
        desc.append(f"课程号_课序号: {self.courseid}")
        desc.append(f"课程名称: {self.name} \n{course['englishCourseName']}")
        desc.append(f"教师: {self.teacher}")
        desc.append(f"学分: {course['unit']}")

        desc.append(f"课程属性: {course['coursePropertiesName']}")
        if course['courseCategoryName']:
            desc.append(f"课程类别: {course['courseCategoryName']}")

        desc.append(f"选课状态: {course['selectCourseStatusName']}")
        
        
        desc.append(f"上课地点: {self.location[0]} / {self.location[1]} / {self.location[2]}")
        desc.append(f"上课周数: {tmp_tapl['weekDescription']} \n {tmp_tapl['classWeek']}")
        desc.append(f"上课星期: {self.weekday}")
        desc.append(f"上课节数: {', '.join(map(str, self.sections))}")
        # restrictedCondition
        if course['restrictedCondition']:
            desc.append(f"选课限制: {course['restrictedCondition']}")
        if course['pkbz']:
            desc.append(f"排课备注: {course['pkbz']}")
            
        self.description = "\n".join(desc)
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
        time_table = time_table_huaxi
        if self.location[0] == "江安":
            time_table = time_table_jiangan
        
        return (time_table[self.sections[0]][0], time_table[self.sections[-1]][1])

    def course_to_events(self):
        events = []
        for i in range(len(self.weeks)):
            week = self.weeks[i]
            # we know week and weekday, so we can calculate the date
            date = self.get_date_of_week(week)
            event = icalendar.Event()
            if self.no_schedule:
                extra_desc = ""
            else:
                extra_desc = f"本周是第 {week} 周 | 课程进度 {i+1}/{len(self.weeks)} 节\n"
            event.add('summary', self.name)
            event.add('location', self.location[0] + " " + self.location[1] + " " + self.location[2])
            event.add('description', extra_desc + self.description )
            start_time = datetime.datetime.combine(date, datetime.datetime.strptime(self.get_section_period()[0], "%H:%M").time())
            end_time = datetime.datetime.combine(date, datetime.datetime.strptime(self.get_section_period()[1], "%H:%M").time())
            # 添加时区信息（中国标准时间 CST = UTC+8）
            event.add('dtstart', start_time, parameters={'TZID': 'Asia/Shanghai'})
            event.add('dtend', end_time, parameters={'TZID': 'Asia/Shanghai'})
            events.append(event)

        return events
