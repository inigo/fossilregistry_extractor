import json
import sys
import re

import pandas as pd
import pdfplumber as pdfplumber

from fossilregistryextractor.base_converter import BaseConverter


# Tables 1 and 2 are exploration drilling and field development drilling - no numbers
# Tables 3 and 4 are about drilling meter performance - I don't know what this is
# Tables 6 and 7 are about permits
# Table 8: Oil/condensate, oil gas and natural gas production (raw gas) 2020 is a summary
# Table 9: Oil and gas production from 2016 to 2020 is a summary
# * Table 10 is interesting - breakdown of individual fields
# Oil production (including condensate from natural gas production) and oil gas production of the fields in 2020
# Table 11 (Distribution of oil production from 2018 to 2020 by production area) is a summary of 10
# Table 12 (Annual production 2019 and 2020 of the most productive oil fields) is a summary of 10
# Table 13 (Natural gas and petroleum gas production from 2016 to 2020.) is a summary
# * Table 14 is interesting (Natural gas production in the fields in 2020 (raw gas without petroleum gas)
# Tables 15 and 16 are summaries
# * Table 17 (oil reserves by region) is interesting
# * Table 18 (natural raw gas reserves by region) is interesting
# * Table 19 (natural clean gas reserves by region) is interesting
# Table 20 (Shares of energy sources in primary energy consumption) is irrelevant
# Table 21 (Characteristics of German natural gas storage) is a summary
# Table 22 (Underground gas storage by federal state) is a summary
# * Table 23 (Natural gas pore storage) is interesting
# * Table 24a (Natural gas cavern storage in operation) is interesting
# * Table 24b (Natural gas cavern storage in planning or under construction) is interesting
# * Table 25 (Cavern storage for crude oil, petroleum products and liquid gas) is interesting
class GermanyConverter(BaseConverter):
    def process_file(self, filename):
        pdf = pdfplumber.open(filename)

        all_json = []

        last_df = None
        last_purpose = None
        i = 0
        for page in pdf.pages:
            print(f"Processing page {i}")
            i = i + 1
            table = page.extract_table()
            text = page.extract_text()
            is_continuation = self._is_continuation(text)

            if last_df is not None and not is_continuation:
                table_as_json_obj = self._to_json(last_df)
                all_json.append({"purpose": last_purpose, "data": table_as_json_obj})
                last_df = None
                last_purpose = None

            purpose = self._identify_table_purpose(text)
            headings = self._identify_headings(text)
            if table is not None and purpose != "" and headings:
                data_rows = self._filter_to_data(table)
                df = pd.DataFrame(data_rows, columns=headings)
                df["Country"] = "Germany"
                df["Country"] = df["Country"].astype("string")
                self._convert_dataframe_in_place(df)

                if is_continuation:
                    combined_df = pd.concat([last_df, df])
                    last_df = combined_df
                else:
                    last_df = df
                    last_purpose = purpose

        pdf.close()
        return json.dumps(all_json, ensure_ascii=False)

    def process_page(self, page):
        table = page.extract_table()
        text = page.extract_text()
        headings = self._identify_headings(text)
        data_rows = self._filter_to_data(table)
        if headings:
            df = pd.DataFrame(data_rows, columns=headings)
            df["Country"] = "Germany"
            df["Country"] = df["Country"].astype("string")
            return df
        else:
            return None

    @staticmethod
    def _identify_headings(text):
        start = text[0:100]
        if not "Tab" in start:
            return []

        # Erdgas Kavernenspeicher - Natural gas stored in caverns
        # "In Betrieb" is in operation, "In Planung oder Bau" is in planning or construction
        if "Erdgas" in start and "Kavernenspeicher" in start:
            # "Speicher", "Bundesland", "Betreiber / Eigentümer", "Anzahl Einzelspeicher", "Teufe", "Speicher formation", "Gesamt volumen", "max. nutzbares Arbeitsgas", "Arbeitsgas nach Endausbau", "Plateau-Entnahmerate"
            return ["Storage", "State", "Operator", "Number of storage tanks", "Depth", "Geologic formation", "Total volume", "Max usable gas", "Gas after completion", "Plateau withdrawal rate"]
        # Mineralölprodukte Kavernenspeicher - Crude oil, petroleum products and liquid gas stored in caverns
        elif "Mineralölprodukte" in start and "Kavernenspeicher" in start:
            # "Speicher", "Bundesland", "Gesellschaft", "Speichertyp", "Teufe", "Anzahl Einzelspeicher", "Füllung", "Zustand"
            return ["Storage", "State", "Company", "Storage type", "Depth", "Number of storage tanks", "Filling", "Status"]
        #  Natural gas storage reservoirs
        elif "Erdgas" in start and "Porenspeicher" in start:
            # "Speicher", "Bundesland", "Betreiber / Eigentümer", "Speichertyp", "Teufe", "Speicherformation", "Gesamt volumen", "max. nutzbares Arbeitsgas", "Arbeitsgas nach Endausbau", "Plateau-Entnahmerate"
            return ["Storage", "State", "Operator", "Storage type", "Depth", "Geologic formation", "Total volume", "Max usable gas", "Gas after completion", "Plateau withdrawal rate"]
        # Clean gas reserves or Raw gas reserves or Oil reserves
        elif (("Reingas" in start or "Rohgas" in start) and "Erdgasreserven" in start) or "Erdölreserven" in start:
            # Bundesland/Gebie; Reserven am 1. Januar 2020: sicher, wahrsch, gesamt; Produktion 2020; Reserven am 1. Januar 2021: sicher, wahrsch, gesamt
            return [ "State/Territory", "Certain reserves 2020", "Probable reserves 2020", "Total reserves 2020", "Production 2020", "Certain reserves 2021", "Probable reserves 2021", "Total reserves 2021" ]
        elif "Erdölförderung" in start and "der Felder" in start:
            # Land, Feld, Fundjahr, Operator, Erdölund Kondensatförderung 2020, Erdölund Kondensatförderung kumulativ, Erdölgasförderung 2020, Erdölgasförderung kumulativ, Sonden
            return [ "Country", "Field", "Year of discovery", "Operator", "Oil and condensate production 2020", "Oil and condensate production cumulative", "Oil gas production 2020", "Oil gas production cumulative", "Probes" ]
        elif "Erdgasförderung" in start and "der Felder" in start:
            # Land, Feld, Fundjahr, Operator, Erdgasförderung 2020, Erdgasförderung kumulativ, Sonden
            # However "Erdgasförderung kumulativ" is not written in order in the PDF - ignoring for now
            return [ "Country", "Field", "Year of discovery", "Operator", "Natural gas production 2020", "Probes" ]
            # Goes on to next page!
        else:
            return []

    @staticmethod
    def _identify_table_purpose(text):
        start = text[0:100]
        if "Erdgas" in start and "Kavernenspeicher" in start and "In Betrieb" in start:
            return "Natural gas storage caverns (planned)"
        elif "Erdgas" in start and "Kavernenspeicher" in start and "In Betrieb" in start:
            return "Natural gas storage caverns (operating)"
        elif "Mineralölprodukte" in start and "Kavernenspeicher" in start:
            return "Crude oil, petroleum products and liquid gas storage caverns"
        elif "Erdgas" in start and "Porenspeicher" in start:
            return "Natural gas storage reservoirs"
        elif "Reingas" in start and "Erdgasreserven" in start:
            return "Clean gas reserves"
        elif "Rohgas" in start and "Erdgasreserven" in start:
            return "Raw gas reserves"
        elif "Erdölreserven" in start:
            return "Oil reserves"
        elif "Erdgasförderung" in start and "der Felder" in start:
            return "Natural gas production by field"
        else:
            return ""

    @staticmethod
    def _is_continuation(text):
        start = text[0:100]
        return "Fortsetzung" in start

    def _filter_to_data(self, table):
        def remove_blanks(row): return [cell for cell in row if cell is not None]
        result = [remove_blanks(row) for row in table if self.any_numeric(row) and row[0] != "" and row[0] is not None]
        return result

    def any_numeric(self, row):
        return any([self.is_numeric(item) for item in row if item is not None])

    def all_numeric(self, row):
        return all([self.is_numeric(item) for item in row if item is not None and item!="" and item!="-"])

    @staticmethod
    def is_numeric(s):
        return re.match(r"^[\d ,]+$", s) is not None

    @staticmethod
    def _to_json(dataframe):
        out = dataframe.to_json(orient="records", date_format="iso")
        return json.loads(out)

    def _convert_dataframe_in_place(self, df):
        for c in df.columns:
            if (self.all_numeric(df[c])):
                df[c] = df[c].replace(r"^-$", None, regex=True) \
                    .replace(r"[ ,]", "", regex=True) \
                    .astype("float")


if __name__ == '__main__':
    GermanyConverter().process_and_save_file(sys.argv[1])
