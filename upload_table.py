import gspread
import sqlite3
from oauth2client.service_account import ServiceAccountCredentials
from brm import db_name


with sqlite3.connect(db_name) as conn:
    cursor = conn.cursor()
    query = cursor.execute("""
    select results.brevet_date, distance, title, rider_names, result from results
    join riders on results.rider_id = riders.rider_id
    join brevets on brevets.brevet_date = results.brevet_date
    order by results.brevet_date""")

    cells = []
    riders = set()

    for row_num, row in enumerate(query, 1):
        col_num = 0
        newbie = 0
        for col_num, cell in enumerate(row, 1):
            if col_num == 4:
                cell = cell.split('|')[-1].split(' ')
                cell = cell[0] + ' ' + cell[1].title()
                if cell in riders:
                    newbie = 0
                else:
                    newbie = 1
                    riders.add(cell)
            cells.append(gspread.Cell(row_num, col_num, cell))
        cells.append(gspread.Cell(row_num, col_num + 1, newbie))

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)
sheet = client.open("vssr").worksheet('brm')
sheet.clear()

sheet.update_cells(cells)
