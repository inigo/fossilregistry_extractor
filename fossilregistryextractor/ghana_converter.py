import json
import sys

import pandas as pd
import pdfplumber as pdfplumber


# Extract a table from the first page of a PDF, formatted as the Ghana OCTP files are
# See test_ghana_conversion.py for an example of the table format
class GhanaConverter:
    def process_and_save_file(self, filename):
        table_as_json_string = self.process_file(filename)
        output_filename = filename.replace(".pdf", ".json")
        with open(output_filename, "w") as outfile:
            outfile.write(table_as_json_string)

    def process_file(self, filename):
        table = self._extract_table(filename)
        table_as_json_obj = self._convert_table(table)
        return json.dumps(table_as_json_obj)

    @staticmethod
    def _extract_table(filename):
        pdf = pdfplumber.open(filename)
        page = pdf.pages[0]
        return page.extract_table()

    @staticmethod
    def _convert_table(table):
        # Skipping the first row, which is a generic label; using the second row as the column headers
        df = pd.DataFrame(table[2:], columns=table[1])
        # Remove the newline characters from the column headers
        df.columns = df.columns.str.replace('\n', '')

        # Convert the Period to a date (e.g. from 'January, 2018' to '2018-01-01')
        df["Period"] = df["Period"].astype('datetime64[ns]')
        # Convert all remaining columns to floats, doing data cleansing on the numbers at the same time
        obj_columns = df.select_dtypes(include=object).columns.tolist()
        df[obj_columns] = df[obj_columns] \
            .replace(r"^-$", None, regex=True) \
            .replace(r",", "", regex=True) \
            .astype("float")

        out = df.to_json(orient="records", date_format="iso")
        return json.loads(out)


if __name__ == '__main__':
    GhanaConverter().process_and_save_file(sys.argv[1])
