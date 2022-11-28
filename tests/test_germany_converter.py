import unittest
import pdfplumber

from fossilregistryextractor.germany_converter import GermanyConverter


class TestGermanyConverter(unittest.TestCase):
    gc = GermanyConverter()
    filename = "pdfs/germany/Jahresbericht2020.pdf"

    def test_process_all(self):
        json_output = self.gc.process_file(self.filename)
        self.assertIn('"Field": "A6 / B4"', json_output, "Could not find expected name of field")
        self.assertIn('"purpose": "Natural gas production by field",', json_output, "Could not find expected purpose")

    def test_process_table_14(self):
        pdf = pdfplumber.open(self.filename)
        df = self.gc.process_page(pdf.pages[31])
        self.assertEqual("A6 / B4", df["Field"][0], )
        self.assertEqual("Apeldorn", df["Field"][19])
        pdf.close()


if __name__ == '__main__':
    unittest.main()
