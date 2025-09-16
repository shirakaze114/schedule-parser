from school_paser import SchoolParser
from bs4 import BeautifulSoup

parser = SchoolParser()

def parse_html(html: str):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"class": "table table-striped table-bordered"})
    # read header
    header_cols = [element.text.strip() for element in table.find_all("tr")[0].find_all("th")]

    print(header_cols)  # Print the header columns for debugging
    parser.set_header(header_cols)

    rows = table.find_all("tr")[1:]  # skip the header
    
    for row_index in range(len(rows)):
        row = rows[row_index]

        cols = [element.text.strip() for element in row.find_all("td")]
        if len(cols) == 2:
            new_index = row_index
            new_cols = []
            while True:
                new_index-=1
                new_cols = [element.text.strip() for element in rows[new_index].find_all("td")]
                if len(new_cols) != 2:
                    break

            new_cols[15] = cols[0]
            new_cols[16] = cols[1]
            cols = new_cols


        #['203170020', '大学化学（Ⅴ）', '日历\n\n李建梅（无）', '大纲\n\n中文大纲\n\n英文大纲', '04', '2', '必修', '', '', '李建梅*', '正常', '置入', '', '', '', '3-18周 / 星期三 / 5-6节', '江安 / 一教B座 / B104']
        print(cols)  # Print the extracted columns for debugging
        #print(parser.curriculum_parser(time_str=cols[15]))
        parser.col_parser(cols)

        
        
def main():
    html = open("本学期课程表.html", "r", encoding="utf-8").read()
    #print(html)
    parse_html(html)
    parser.generate_ics()
    




if __name__ == "__main__":
    main()