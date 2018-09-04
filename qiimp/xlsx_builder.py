import collections
from random import randrange
import re
import unicodedata
import xlsxwriter
import yaml

import qiimp.schema_builder
import qiimp.xlsx_basics as xlsxbasics
import qiimp.xlsx_metadata_grid_builder
import qiimp.xlsx_validation_builder
import qiimp.xlsx_static_grid_builder
import qiimp.xlsx_dynamic_grid_builder

# Ensures defaultdicts are represented as nice yaml rather than nasty (see https://stackoverflow.com/a/19323121 )
from yaml.representer import Representer
yaml.add_representer(collections.defaultdict, Representer.represent_dict)


def write_workbook(study_name, schema_dict, form_dict, metadata_wizard_settings):
    num_allowable_samples = 1000
    # TODO: someday: either expand code to use num_samples and add real code to get in from interface, or take out unused hook
    num_samples = 0
    num_columns = len(schema_dict.keys())
    a_regex_handler = metadata_wizard_settings.regex_handler

    # create workbook
    file_base_name = slugify(study_name)
    file_name = '{0}_{1}.xlsx'.format(file_base_name, randrange(1000, 9999))
    output_path = metadata_wizard_settings.get_output_path(file_name)
    workbook = xlsxwriter.Workbook(output_path, {'strings_to_numbers': False,
                                               'strings_to_formulas': True,
                                               'strings_to_urls': True})

    # write metadata worksheet
    phi_renamed_schema_dict = qiimp.schema_builder.rewrite_field_names_with_phi_if_relevant(schema_dict)
    metadata_worksheet = xlsxbasics.MetadataWorksheet(workbook, num_columns, num_samples, a_regex_handler,
                                                      num_allowable_samples=num_allowable_samples)
    qiimp.xlsx_metadata_grid_builder.write_metadata_grid(metadata_worksheet, phi_renamed_schema_dict,
                                                                   DescriptionWorksheet.get_sheet_name())

    # write validation worksheet
    validation_worksheet = qiimp.xlsx_static_grid_builder.ValidationWorksheet(workbook, num_columns,
                                                                                        num_samples, a_regex_handler)
    index_and_range_str_tuple_by_header_dict = qiimp.xlsx_static_grid_builder.write_static_validation_grid_and_helpers(
        validation_worksheet, phi_renamed_schema_dict)
    qiimp.xlsx_dynamic_grid_builder.write_dynamic_validation_grid(
        validation_worksheet, index_and_range_str_tuple_by_header_dict)

    # write descriptions worksheet
    descriptions_worksheet = DescriptionWorksheet(workbook, num_columns, num_samples, a_regex_handler)
    xlsxbasics.write_header(descriptions_worksheet, "field name", 0)
    xlsxbasics.write_header(descriptions_worksheet, "field description", 1)
    sorted_keys = xlsxbasics.sort_keys(phi_renamed_schema_dict)
    for field_index, field_name in enumerate(sorted_keys):
        row_num = field_index + 1 + 1  # plus 1 to move past name row, and plus 1 again because row nums are 1-based
        field_specs_dict = phi_renamed_schema_dict[field_name]
        message = qiimp.xlsx_validation_builder.get_field_constraint_description(field_specs_dict, a_regex_handler)
        descriptions_worksheet.worksheet.write("A{0}".format(row_num), field_name, metadata_worksheet.header_format)
        descriptions_worksheet.worksheet.write("B{0}".format(row_num), message)

    # write schema worksheet--note, don't use the phi_renamed_schema_dict but the original schema_dict
    schema_worksheet = xlsxbasics.create_worksheet(workbook, xlsxbasics.SheetNames.schema.value)
    schema_worksheet.write_string("A1", yaml.dump(schema_dict, default_flow_style=False))
    schema_worksheet.hide()

    # write form worksheet
    form_worksheet = xlsxbasics.create_worksheet(workbook, xlsxbasics.SheetNames.form.value)
    form_worksheet.write_string("A1", yaml.dump(form_dict, default_flow_style=False))
    form_worksheet.hide()

    # write readme worksheet
    readme_format = workbook.add_format({'align': 'left', 'valign': 'top'})
    readme_format.set_text_wrap()
    readme_worksheet = xlsxbasics.create_worksheet(workbook, xlsxbasics.SheetNames.readme.value)
    readme_worksheet.set_column(0, 0, 100)  # Width of column A set to 100.
    tutorial_hyperlink_str = "=HYPERLINK(\"{0}\", \"Click here for instructions on using this spreadsheet.\")".format(
                                       metadata_wizard_settings.TUTORIAL_LINK)

    readme_worksheet.write_formula(0,0, tutorial_hyperlink_str,
                                   # TODO: someday: centralize link format definitions.
                                   # this link format is a copy-paste of the one in
                                   # xlsx_dynamic_grid_builder._write_dynamic_name_link_col ; assuming we want
                                   # all the link formats in the spreadsheet to look the same, they should be defined
                                   # in one central place.
                                   xlsxbasics.make_format(workbook, {'font_color': 'blue', 'underline': 1}))
    readme_worksheet.write_string('A3', metadata_wizard_settings.make_readme_text(), readme_format)

    # close workbook
    workbook.close()
    return file_name


class DescriptionWorksheet(xlsxbasics.MetadataWorksheet):
    @classmethod
    def get_sheet_name(cls):
        return xlsxbasics.SheetNames.data_dictionary.value

    def __init__(self, workbook, num_attributes, num_samples, a_regex_handler):
        super().__init__(workbook, num_attributes, num_samples, a_regex_handler, make_sheet=False)

        SHEET_NAME = self.get_sheet_name()
        self.worksheet = xlsxbasics.create_worksheet(self.workbook, SHEET_NAME,
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
