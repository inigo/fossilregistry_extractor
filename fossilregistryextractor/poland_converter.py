import json
import sys
import re

import pandas as pd
import pdfplumber as pdfplumber

from .base_converter import BaseConverter


# Extract a long table spread across every page of a PDF, formatted as the Poland natural gas files
# Skips the subheader rows that are just totals for the rows beneath them
class PolandConverter(BaseConverter):
    def process_file(self, filename):
        pdf = pdfplumber.open(filename)
        dataframes = [self.to_dataframe(p) for p in pdf.pages]
        pdf.close()
        combined_dataframe = pd.concat(dataframes)
        table_as_json_obj = self._to_json(combined_dataframe)
        return json.dumps(table_as_json_obj, ensure_ascii=False)

    def to_dataframe(self, page):
        table = page.extract_table()
        return self._convert_table(table)

    def _convert_table(self, table):
        data_rows = self._filter_to_data(table)
        header_row = self._choose_header(data_rows[0])

        df = pd.DataFrame(data_rows, columns=header_row)
        df["Country"] = "Poland"
        df["Country"] = df["Country"].astype("string")
        # PDF has values like Z, T, K to indicate status
        df["State of development"] = df["State of development"].apply(self._lookup_status).astype("string")
        df["County"] = df["County"].apply(self._convert_county)
        # "Numeric" values are actually sometimes multiple, and have the letter "s" to indicate subeconomic
        cols_to_convert = list(filter(lambda s: "Resources" in s or "Output" in s, df.columns))
        for c in cols_to_convert:
            df[c] = df[c].apply(self._convert_value)
        return df

    @staticmethod
    def _convert_county(counties):
        return list(map(lambda s: s.strip(), counties.replace("\n", "").replace("-", "").split(",")))

    @staticmethod
    def _convert_value(value):
        def try_to_float(n):
            try:
                return float(n)
            except ValueError:
                return None

        def convert_fn(val):
            n_as_str = re.sub(r"[^\d.-]", "", val)
            n = try_to_float(n_as_str)
            is_subeconomic = "s" in val
            return {"value": n, "is_subeconomic": is_subeconomic}
        values = filter(lambda s: re.search(r"[\ds-]", s), value.split("\n"))
        return list(map(convert_fn, values))

    # Identify which set of headers is being used - it is hard to retrieve these automatically because of the
    # various merged columns
    @staticmethod
    def _choose_header(first_data_row):
        if len(first_data_row) == 7:
            return ["Number", "Name of field", "State of development", "Resources anticipated economic", "Resources economic", "Output", "County"]
        elif len(first_data_row) == 9:
            return ["Number", "Name of field", "State of development", "Resources anticipated Total",
                    "Resources anticipated A+B", "Resources anticipated C", "Resources economic", "Output", "County"]
        else:
            raise Exception(f"Unexpected number of columns {len(first_data_row)} - check definition of headers and adjust")

    StatusLookup = {
        "B": "Building Mine or Prepared or Trial",  # for solid minerals - mine in a building process, for fuels - prepared for the exploitation or a trial period of the exploitation
        "E": "Exploited",  # exploited
        "G": "Underground Natural Gas Storage",  # underground natural gas storage facilities
        "M": "Crossed Out Of Annual Report",  # deposit crossed out of the annual report of mineral resources during an analyzed period
        "P": "Covered By Preliminary Exploration",  # deposit covered by the preliminary exploration (in C2+D category, for fuels ??? in C category)
        "R": "Covered by Detailed Exploration",  # deposit covered by the detailed exploration (in A+B+C1 category, for fuels ??? in A+B category)
        "Z": "Abandoned",  # abandoned deposit
        "T": "Exploited Temporarily",  # deposit exploited temporarily
        "K": "Changed Raw Material",  # change of the raw material in a deposit
    }

    def _lookup_status(self, status_code):
        return self.StatusLookup[status_code]

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
