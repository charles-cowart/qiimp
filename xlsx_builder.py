import collections
import re
import unicodedata
import xlsxwriter
import yaml

import xlsx_basics
import xlsx_metadata_grid_builder
import xlsx_validation_builder
import xlsx_static_grid_builder
import xlsx_dynamic_grid_builder

# Ensures defaultdicts are represented as nice yaml rather than nasty (see https://stackoverflow.com/a/19323121 )
from yaml.representer import Representer
yaml.add_representer(collections.defaultdict, Representer.represent_dict)


def write_workbook(study_name, schema_dict, a_regex_handler, form_dict, readme_text):
    num_allowable_samples = 1000
    # TODO: someday: either expand code to use num_samples and add real code to get in from interface, or take out unused hook
    num_samples = 0
    num_columns = len(schema_dict.keys())

    # create workbook
    file_base_name = slugify(study_name)
    file_name = '{0}.xlsx'.format(file_base_name)
    workbook = xlsxwriter.Workbook(file_name, {'strings_to_numbers': False,
                                               'strings_to_formulas': True,
                                               'strings_to_urls': True})

    # write metadata worksheet
    metadata_worksheet = xlsx_basics.MetadataWorksheet(workbook, num_columns, num_samples, a_regex_handler,
                                                       num_allowable_samples=num_allowable_samples)
    xlsx_metadata_grid_builder.write_metadata_grid(metadata_worksheet, schema_dict)

    # write validation worksheet
    validation_worksheet = xlsx_static_grid_builder.ValidationWorksheet(workbook, num_columns, num_samples,
                                                                        a_regex_handler)
    index_and_range_str_tuple_by_header_dict = xlsx_static_grid_builder.write_static_validation_grid_and_helpers(
        validation_worksheet, schema_dict)
    xlsx_dynamic_grid_builder.write_dynamic_validation_grid(
        validation_worksheet, index_and_range_str_tuple_by_header_dict)

    # write descriptions worksheet
    descriptions_worksheet = DescriptionWorksheet(workbook, num_columns, num_samples, a_regex_handler)
    xlsx_basics.write_header(descriptions_worksheet, "field name", 0)
    xlsx_basics.write_header(descriptions_worksheet, "field description", 1)
    sorted_keys = xlsx_basics.sort_keys(schema_dict)
    for field_index, field_name in enumerate(sorted_keys):
        row_num = field_index + 1 + 1  # plus 1 to move past name row, and plus 1 again because row nums are 1-based
        field_specs_dict = schema_dict[field_name]
        message = xlsx_validation_builder.get_field_constraint_description(field_specs_dict, a_regex_handler)
        descriptions_worksheet.worksheet.write("A{0}".format(row_num), field_name, metadata_worksheet.bold_format)
        descriptions_worksheet.worksheet.write("B{0}".format(row_num), message)

    # write schema worksheet
    schema_worksheet = xlsx_basics.create_worksheet(workbook, "metadata_schema")
    schema_worksheet.write_string("A1", yaml.dump(schema_dict, default_flow_style=False))

    # write form worksheet
    form_worksheet = xlsx_basics.create_worksheet(workbook, "metadata_form")
    form_worksheet.write_string("A1", yaml.dump(form_dict, default_flow_style=False))

    # write readme worksheet
    form_worksheet = xlsx_basics.create_worksheet(workbook, "readme")
    form_worksheet.write_string("A1", readme_text)

    # close workbook
    workbook.close()
    return file_name


class DescriptionWorksheet(xlsx_basics.MetadataWorksheet):
    def __init__(self, workbook, num_attributes, num_samples, a_regex_handler):
        super().__init__(workbook, num_attributes, num_samples, a_regex_handler, make_sheet=False)

        self.worksheet = xlsx_basics.create_worksheet(self.workbook, "field descriptions",
                                                      self._permissive_protect_options)


# very slight modification of django code at https://github.com/django/django/blob/master/django/utils/text.py#L413
def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)
