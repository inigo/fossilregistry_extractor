import unittest

from fossilregistryextractor.ghana_converter import GhanaConverter


class TestGhanaConversion(unittest.TestCase):
    # Note the typo "Non-Asssociated" in this test table from the PDF; also the inconsistent whitespace

    example_table = [['2018 OCTP PRODUCTION', None, None, None, None, None, None, None],
                     ['Period', 'Oil Production \n(bbl)', 'Associated Gas \nProduction \n(MMscf)',
                      'Non - Asssociated \nGas Production \n(MMscf)', 'Gas Re-injected \n(MMscf)', 'Fuel Gas (MMscf)',
                      'Flared \nGas(MMscf)', 'Sales Gas \n(MMscf)'],
                     ['January, 2018', '1,098,754.50', '1,666.48', '-', '1,139.50', '372.82', '154.16', '0'],
                     ['February, 2018', '909,194.42', '1,425.87', '-', '1,025.40', '327.99', '72.48', '0'],
                     ['March, 2018', '911,716.90', '1,503.66', '-', '1,115.26', '346.76', '41.62', '0'],
                     ['April, 2018', '801,360.61', '1,366.06', '-', '1,014.31', '335.66', '16.09', '0'],
                     ['May, 2018', '778,355.43', '1,356.07', '-', '974.71', '347.82', '33.54', '0'],
                     ['June, 2018', '787,115.61', '1,409.62', '188.49', '1,036.77', '338.81', '34.04', '0'],
                     ['July, 2018', '810,709.34', '1,493.70', '400.89', '1,126.89', '350.45', '370.83', '0'],
                     ['August, 2018', '799,909.38', '1,510.95', '754.41', '1,131.56', '357.12', '72.19', '661.44'],
                     ['September, 2018', '734,348.44', '1,335.99', '520.07', '992.76', '357.03', '10.18', '445.2'],
                     ['October, 2018', '709,628.53', '1,299.86', '914.67', '880.4', '363.25', '67.39', '874.15'],
                     ['November, 2018', '818,248.15', '1,402.63', '2,195.54', '1,085.65', '347.05', '36.23', '2,083.29'],
                     ['December, 2018', '956,977.75', '1,504.18', '2,162.00', '1,198.70', '360.28', '9.58', '2,045.91']]

    def test_process(self):
        json_output = GhanaConverter().process_file("pdfs/2018-OCTP-Productions.pdf")
        self.assertIn('"Period": "2018-', json_output, "Could not find Period")
        self.assertIn('"Oil Production (bbl)": 1098754.5', json_output, "Could not find Oil Production with numeric value")

    def test_extraction(self):
        table = GhanaConverter._extract_table("pdfs/2018-OCTP-Productions.pdf")
        self.assertEqual('2018 OCTP PRODUCTION', table[0][0])
        self.assertEqual('Period', table[1][0])
        self.assertEqual('2,045.91', table[-1][-1])

    def test_convert_table(self):
        r = GhanaConverter._to_json(GhanaConverter()._convert_table(self.example_table))
        self.assertEqual(r[0]["Period"], '2018-01-01T00:00:00.000')
        self.assertEqual(r[0]['Fuel Gas (MMscf)'], 372.82)
        self.assertEqual(r[1]['Oil Production (bbl)'], 909194.42)

    def test_identify_region(self):
        self.assertEqual(GhanaConverter._identify_field("2018 OCTP PRODUCTION"), "OCTP")
        self.assertEqual(GhanaConverter._identify_field("OCTP / Sankofa-Gye Nyame Production for the Year 2019"), "OCTP / Sankofa-Gye Nyame")
        self.assertEqual(GhanaConverter._identify_field("2018 Jubilee Production"), "Jubilee")
        self.assertEqual(GhanaConverter._identify_field("Jubilee Production for the Year 2019"), "Jubilee")
        self.assertEqual(GhanaConverter._identify_field("2018 TEN PRODUCTION"), "TEN")
        self.assertEqual(GhanaConverter._identify_field("TEN Production for the Year 2019"), "TEN")

if __name__ == '__main__':
    unittest.main()
