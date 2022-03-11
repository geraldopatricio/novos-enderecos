from services.metasingleton import MetaSingleton
from services.safebox import Safebox
import pyodbc

class SQLServer(metaclass=MetaSingleton):
    connection = None

    def connect(self):
        if self.connection is None:
            server = Safebox.get_secret("DB-RASTREAMENTOCARTOES-HOST")
            database = Safebox.get_secret("DB-RASTREAMENTOCARTOES-DATABASE")
            username = Safebox.get_secret("DB-RASTREAMENTOCARTOES-RDKNEWENDCARDDEVOLVIDO-USERNAME")
            password = Safebox.get_secret("DB-RASTREAMENTOCARTOES-RDKNEWENDCARDDEVOLVIDO-PASSWORD")
            string_connection = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            self.connection = pyodbc.connect(string_connection)
            self.cursorobj = self.connection.cursor()
        return self.cursorobj

    def close(self):
        self.connection.close()
