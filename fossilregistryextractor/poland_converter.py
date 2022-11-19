import json
import sys

import pandas as pd
import pdfplumber as pdfplumber

from base_converter import BaseConverter


# Extract a long table spread across every page of a PDF, formatted as the Poland natural gas files
# Skips the subheader rows that are just totals for the rows beneath them
class PolandConverter(BaseConverter):
    def process_file(self, filename):
        pdf = pdfplumber.open(filename)
        dataframes = [self.to_dataframe(p) for p in pdf.pages]
        combined_dataframe = pd.concat(dataframes)
        table_as_json_obj = self._to_json(combined_dataframe)
        return json.dumps(table_as_json_obj)

    def to_dataframe(self, page):
        table = page.extract_table()
        return self._convert_table(table)

    def _convert_table(self, table):
        data_rows = self._filter_to_data(table)
        header_row = self._choose_header(data_rows[0])

        df = pd.DataFrame(data_rows, columns=header_row)
        df["Country"] = "Poland"
        df["Country"] = df["Country"].astype("string")

        return df

    # Identify which set of headers is being used - it is hard to retrieve these automatically because of the
    # various merged columns
    @staticmethod
    def _choose_header(first_data_row):
        if len(first_data_row) == 7:
            return ["Number", "Name of deposit", "State of development", "Resources anticipated economic", "Resources economic", "Output", "County"]
        elif len(first_data_row) == 9:
            return ["Number", "Name of field", "State of development", "Resources anticipated Total",
                    "Resources anticipated A+B", "Resources anticipated C", "Resources economic", "Output", "County"]
        else:
            raise Exception(f"Unexpected number of columns {len(first_data_row)} - check definition of headers and adjust")

    @staticmethod
    def _filter_to_data(table):
        def remove_blanks(row): return [cell for cell in row if cell is not None]
        return [remove_blanks(row) for row in table if row[-1] is not None and row[-1] != '' and row[0] is not None and row[0] != '']

    @staticmethod
    def _to_json(dataframe):
        out = dataframe.to_json(orient="records", date_format="iso")
        return json.loads(out)


if __name__ == '__main__':
    PolandConverter().process_and_save_file(sys.argv[1])
