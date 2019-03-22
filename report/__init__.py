import jinja2

PROFILE_REPORTS = {}

def registe_report(name, report):
    PROFILE_REPORTS[name] = report

class GlobalReport(object):
    """a global report manager, all the report will register its
    information to this manager, and generate report globally
    """
    @staticmethod
    def profile_report_gen():
        for name, report  in PROFILE_REPORTS.items():
            print("generating report for profile", name)
            report.generate_report()

class ProfileReport(object):
    def __init__(self, title=""):
        self._title = title
        self._columns = ['用例名称', '是否通过', '说明']
        self._case_info = []
        self._start_time = ""
        self._end_time = ""
        self._total= 0
        self._succeed = 0
        self._fail = 0
        registe_report(self._title, self)

    def set_title(self, title):
        self._title = title

    def add_case_info(self, case, result, note):
        """normally the result should be limited to ok, and fail,
        so if the result is Boolen, it will be converted to ok and
        fail.
        """
        while True:
            print ("result is:",result)
            if result in ['ok', 'fail']:
                break
            if result in ['True', 'False']:
                result = 'ok' if result=='True' else 'fail'
                break
            break

        self._case_info.append((case, result, note))

    def get_case_info(self):
        return self._case_Info

    def set_start_time(self, start):
        """
        :type start: str
        :param start: the start time of the profile execution
        """
        self._start_time = start

    def set_end_time(self, end):
        """
        :type end: str
        :param end: the complete time of the profile execution
        """
        self._end_time = end

    def _gen_statistic(self):
        self._total = len(self._case_info)
        self._succeed = 0
        self._fail = 0
        for case in self._case_info:
            if case[1] == 'ok':
                self._succeed += 1
            else:
                self._fail += 1

    def generate_report_html(self, report_position):
        templateLoader = jinja2.FileSystemLoader(searchpath="./report")
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "report_template.html"
        template = templateEnv.get_template(TEMPLATE_FILE)
        self._gen_statistic()
        params = {
            "profile": self._title,
            "columns": self._columns,
            "data": self._case_info,
            "start": self._start_time,
            "end": self._end_time,
            "total": self._total,
            "succeed": self._succeed,
            "fail": self._fail
            }
        content = template.render(params)
        
        with open(report_position, "w") as fd:
            fd.write(content)

        print("test report was generated to", report_position)

    def generate_report_text(self, report_position):
        self._gen_statistic()
        params = {
            "profile": self._title,
            "columns": self._columns,
            "data": self._case_info,
            "start": self._start_time,
            "end": self._end_time,
            "total": self._total,
            "succeed": self._succeed,
            "fail": self._fail
            }
        with open(report_position, 'w') as fd:
            s = (
                "{profile} test report\n"
                "start time: {starttime}\n"
                "end time:   {endtime}\n\n"
                ).format(profile=self._title, starttime=self._start_time,
                       endtime=self._end_time)
            
            fd.write(s)

            s = []

            s.append("".join(["%-60s"%column for column in self._columns]))

            s.append("\n")

            for case in self._case_info:
                s.append("".join(["%-60s"%item for item in case]))
                

            fd.write("\n".join(s))
            print("test report was generated to", report_position)

            
            
