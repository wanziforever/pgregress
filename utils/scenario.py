class Command(object):
    def __init__(self):
        pass

class SQLCommand(command):
    def __init__(self, session_tag):
        SQLCommand.__init__(self)
        self.session_tag = session_tag
        self.sql = ''

    def set_sql(self, sql):
        self.sql = sql

    def get_sql(self):
        return sql

    def get_session_tag(self):
        return self.session_tag
    

class Scenario(oject):
    def __init__(self, name):
        self.name = name
        self._commands = []
        self._command_pos = -1

    def add_sql_command(self, cmd):
        self._commands.append(cmd)

    def next_command(self):
        pass

    def is_end(self):
        return False

    def get_name(self):
        return name
    
        
