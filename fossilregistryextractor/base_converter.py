from abc import abstractmethod, ABC


# Parent of the various other converters, providing shared methods
class BaseConverter(ABC):
    def process_and_save_file(self, filename):
        table_as_json_string = self.process_file(filename)
        output_filename = filename.replace(".pdf", ".json")
        with open(output_filename, "w") as outfile:
            outfile.write(table_as_json_string)

    @abstractmethod
    def process_file(self, filename):
        pass
