import unittest

from fossilregistryextractor.poland_converter import PolandConverter


class TestPolandConverter(unittest.TestCase):
    pc = PolandConverter()

    table2020 = [['', None, 'Name of field', 'd', 'The', '-', '', 'Resources', None, None, None, None, None, None, None, None, '', 'Output', 'County'],
     [None, None, None, None, 'state of', None, '', 'exploitable anticipated economic', None, None, None, None, None, None, '', 'economic', None, None, None],
     [None, None, None, None, 'evelop', None, None, 'anticipated sub-economic s', None, None, None, None, None, None, None, None, None, None, None],
     [None, None, None, None, 'ment', None, '', 'Total', '', '', 'A+B', '', '', 'C', '', None, None, None, None],
     ['Total number of fields: 306', None, None, None, None, None, '', '141,643.38', '', '', '66,895.32', '', '', '74,748.06', '', '73,514.38', None, '4,933.98', ''],
     [None, None, None, None, None, None, None, '2,277.13 s', None, None, '35.29 s', None, None, '2,241.84 s', None, None, None, None, None],
     [None, 'number of fields: 5', None, None, None, None, None, '- s', None, None, '- s', None, None, '- s', None, None, None, None, None],
     ['1', None, 'B 21', 'R', None, None, '275.00', None, None, '-', None, None, '275.00', None, None, '261.23', None, '-', 'Bałtyk (off shore)'],
     ['2', None, 'B 3', 'E', None, None, '209.03', None, None, '205.11', None, None, '3.92', None, None, '160.34', None, '8.06', 'Bałtyk (off shore)']
    ]

    table2015 = [['', 'Name of deposit', 'The \nstate of \ndevelop-\nment', 'Resources', None, 'Output', 'County'],
     [None, None, None, 'anticipated \neconomic', 'economic', None, None],
     ['Total number of fields: 292', None, None, '122,820.02', '54,913.68', '5,213.52', ''],
     ['Baltic Sea \nnumber of fields: 4', None, None, '5,021.71', '4,291.06', '18.24', ''],
     ['1', 'B 3', 'E', '113.38', '113.38', '14.69', 'Bałtyk (off shore)'],
     ['2', 'B 4', 'P', '2,686.60', '1,972.40', '-', 'Bałtyk (off shore)'],
     ['3', 'B 6', 'P', '1,792.85', '1,792.85', '-', 'Bałtyk (off shore)']
    ]

    def test_filter_to_data_2015(self):
        data = self.pc._filter_to_data(self.table2015)
        self.assertEqual(3, len(data))
        self.assertEqual('1', data[0][0])
        self.assertEqual('Bałtyk (off shore)', data[0][-1])
        self.assertEqual('Bałtyk (off shore)', data[2][-1])

    def test_filter_to_data_2020(self):
        data = self.pc._filter_to_data(self.table2020)
        self.assertEqual(2, len(data))
        self.assertEqual('1', data[0][0])
        self.assertEqual('Bałtyk (off shore)', data[0][-1])

    def test_choose_headers_2015(self):
        first_row = self.pc._filter_to_data(self.table2015)[0]
        header = self.pc._choose_header(first_row)
        expected_header = ["Number", "Name of deposit", "State of development", "Resources anticipated economic", "Resources economic", "Output", "County"]
        self.assertEqual(expected_header, header)

    def test_choose_headers_2020(self):
        first_row = self.pc._filter_to_data(self.table2020)[0]
        header = self.pc._choose_header(first_row)
        expected_header = ["Number", "Name of field", "State of development", "Resources anticipated Total",
                           "Resources anticipated A+B", "Resources anticipated C", "Resources economic", "Output", "County"]
        self.assertEqual(expected_header, header)

    def test_process(self):
        json_output = self.pc.process_file("pdfs/poland/natural_gas_2020.pdf")
        self.assertIn('"Name of field": "B 21"', json_output, "Could not find expected name of field")


if __name__ == '__main__':
    unittest.main()
