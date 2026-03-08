import datetime

from selenium_courses import get_course_json
from course import Course
from icalendar import Calendar, Event

def main():
    print("Link: https://github.com/shirakaze114/schedule-parser")
    raw_data = get_course_json(1)
    # print(raw_data)

    courses = []

    print("选课总学分:", raw_data['allUnits'])
    courses_index = raw_data['xkxx'][0].keys()
    for index in courses_index:
        course = raw_data['xkxx'][0][index]
        if len(course['timeAndPlaceList']) > 0:
            # 当成多个课程来处理，每个 timeAndPlaceList 的元素都生成一个课程
            for i in range(len(course['timeAndPlaceList'])):
                course_copy = course.copy()
                course_copy['timeAndPlaceList'] = [course['timeAndPlaceList'][i]]
                # print(course_copy)
                courses.append(Course(course_copy))
        else:
            courses.append(Course(course))

    # 生成 iCalendar 文件
    cal = Calendar()
    cal.add('prodid', '-//Schedule Parser//mxgmn//')
    cal.add('version', '2.0')
    #filename schedule-{{timestamp}}.ics
    filename = f"schedule-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.ics"

    for course in courses:
        events = course.course_to_events()
        for event in events:
            cal.add_component(event)
    with open(filename, 'wb') as f:
        f.write(cal.to_ical())

    print(f"课程信息已保存到 {filename} 文件中！")


if __name__ == "__main__":
    main()
