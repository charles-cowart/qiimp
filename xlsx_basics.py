import string
import metadata_package_schema_builder
import regex_handler


# region general functions for working with worksheets and formulas
def get_worksheet_password():
    return ""
    # return "kpcofGs"  # Kingdom phylum class order family Genus species


def create_worksheet(workbook, sheet_name, protect_options=None, num_cols_to_freeze=1):
    worksheet = workbook.add_worksheet(sheet_name)
    # if protect_options is None, default options (allow only selection) will be used
    worksheet.protect(get_worksheet_password(), protect_options)
    worksheet.freeze_panes(1, num_cols_to_freeze)
    return worksheet


def make_format(workbook, format_properties_dict=None, is_locked=True):
    if format_properties_dict is None:
        format_properties_dict = {}
    format_properties_dict['font_name'] = 'Cambria'
    format_properties_dict['locked'] = int(is_locked)
    return workbook.add_format(format_properties_dict)


def get_fix_symbol(is_fixed):
    return "$" if is_fixed else ""


def get_letter(zero_based_letter_index):
    return (string.ascii_lowercase[zero_based_letter_index]).upper()


def get_col_letters(curr_col_index):
    len_alphabet = len(string.ascii_lowercase)
    num_complete_alphabets = curr_col_index // len_alphabet
    if num_complete_alphabets >= len_alphabet:
        max_num_columns = len_alphabet * len_alphabet
        raise ValueError("Having greater than or equal to {0} columns is not supported".format(max_num_columns))

    prefix_letter = "" if num_complete_alphabets == 0 else get_letter(num_complete_alphabets - 1)
    index_within_curr_alphabet = curr_col_index % len_alphabet
    current_letter = get_letter(index_within_curr_alphabet)
    result = "{0}{1}".format(prefix_letter, current_letter)
    return result


def format_range(first_col_index, first_row_index, last_col_index=None, last_row_index=None, sheet_name=None,
                 first_col_fixed=False, first_row_fixed=False, last_col_fixed=None, last_row_fixed=False):
    first_col_letter = get_col_letters(first_col_index)
    second_col_letter = first_col_letter if last_col_index is None else get_col_letters(last_col_index)
    last_row_index = last_row_index if last_row_index is not None else first_row_index
    formatted_sheet_name = "{0}!".format(sheet_name) if sheet_name is not None else ""
    if last_col_index is None and last_col_fixed is None:
        last_col_fixed = first_col_fixed

    first_half_of_range = "{0}{1}{2}{3}".format(get_fix_symbol(first_col_fixed), first_col_letter,
                                                get_fix_symbol(first_row_fixed), first_row_index)
    second_half_of_range = "{0}{1}{2}{3}".format(get_fix_symbol(last_col_fixed), second_col_letter,
                                                 get_fix_symbol(last_row_fixed), last_row_index)

    if second_half_of_range == first_half_of_range:
        second_half_of_range = ""
    else:
        second_half_of_range = ":{0}".format(second_half_of_range)

    return "{0}{1}{2}".format(formatted_sheet_name, first_half_of_range, second_half_of_range)


# NB: can handle array formulas AS LONG AS they work on columns and only return a single cell!
# No array formulas that return ranges and no array formulas that work on rows are supported.
def copy_formula_throughout_range(worksheet, partial_formula_str, first_col_index, first_row_index,
                                  last_col_index=None, last_row_index=None, sheet_name=None,
                                  first_col_fixed=False, first_row_fixed=False,
                                  last_col_fixed=None, last_row_fixed=False,
                                  cell_format=None, is_array_formula=False):

    cell_enumerator = loop_through_range(first_col_index, first_row_index, last_col_index=last_col_index,
                                         last_row_index=last_row_index, sheet_name=sheet_name,
                                         col_fixed=first_col_fixed, row_fixed=first_row_fixed)

    for curr_col_letter, curr_row_index, curr_cell in cell_enumerator:
        completed_formula = partial_formula_str.format(cell=curr_cell, curr_col_letter=curr_col_letter,
                                                       curr_row_index=curr_row_index, first_row_index=first_row_index,
                                                       last_row_index=last_row_index)

        if not is_array_formula:
            worksheet.write_formula(curr_cell, completed_formula, cell_format)
        else:
            worksheet.write_array_formula(curr_cell, completed_formula, cell_format)

    full_range = format_range(first_col_index, first_row_index, last_col_index=last_col_index,
                              last_row_index=last_row_index, first_col_fixed=first_col_fixed,
                              first_row_fixed=first_row_fixed, last_col_fixed=last_col_fixed,
                              last_row_fixed=last_row_fixed)
    return full_range


def loop_through_range(first_col_index, first_row_index, last_col_index=None, last_row_index=None, sheet_name=None,
                       col_fixed=False, row_fixed=False):
    last_col_index = first_col_index if last_col_index is None else last_col_index
    last_row_index = first_row_index if last_row_index is None else last_row_index

    # at outer level, move across columns
    for curr_col_index in range(first_col_index, last_col_index + 1):  # +1 bc range is exclusive of last number!
        curr_col_letter = get_col_letters(curr_col_index)
        # at inner level, move down rows
        for curr_row_index in range(first_row_index, last_row_index + 1):  # +1 bc range is exclusive of last number!
            curr_cell = format_range(curr_col_index, curr_row_index, sheet_name=sheet_name,
                                     first_col_fixed=col_fixed, first_row_fixed=row_fixed)
            yield curr_col_letter, curr_row_index, curr_cell


def sort_keys(schema_dict):
    # sort into alphabetical order
    sorted_keys = sorted(schema_dict.keys())

    # remove the sample_name from its existing place in the list (if any) and then add it back at the FIRST position
    try:
        sorted_keys.remove(metadata_package_schema_builder.SAMPLE_NAME_HEADER)
    except ValueError:
        pass

    # zero means add this back as the very first item in the key array
    sorted_keys.insert(0, metadata_package_schema_builder.SAMPLE_NAME_HEADER)
    return sorted_keys


# end region


class MetadataWorksheet(object):
    # I think the column range available for worksheets is 'A:XFD'

    def __init__(self, workbook, num_attributes, num_samples, a_regex_handler, make_sheet=True, num_allowable_samples=1000):
        """

        :type a_regex_handler: regex_handler.RegexHandler
        """

        self.workbook = workbook
        self.metadata_sheet_name = "metadata"
        self.regex_handler = a_regex_handler
        self.num_allowable_samples = num_allowable_samples
        self._num_field_columns = num_attributes
        # _num_samples not currently used; here as a hook for some of Austin's future requests
        self._num_samples = num_samples

        self.bold_format = make_format(workbook, {'bold': True})
        self.hidden_cell_setting = {'hidden': 1}
        self._permissive_protect_options = {
            'objects': False,
            'scenarios': False,
            'format_cells': True,
            'format_columns': True,
            'format_rows': True,
            'insert_columns': False,
            'insert_rows': False,
            'insert_hyperlinks': False,
            'delete_columns': False,
            'delete_rows': False,
            'select_locked_cells': True,
            'sort': False,
            'autofilter': False,
            'pivot_tables': False,
            'select_unlocked_cells': True
        }

        self.sample_id_col_index = 0  # column indices are zero-based
        self.name_row_index = 1  # row indices are one-based
        # I've tested 250, 1000, 1500, 2000 and 10,000; at 10,000 rows of formulas, the workbook bogs down horribly.
        # Haven't checked anything in between ...
        self.last_allowable_row_for_sample_index = self.num_allowable_samples + self.name_row_index
        self.first_data_row_index = self.name_row_index + 1
        self.last_data_row_index = self.last_allowable_row_for_sample_index
        self.first_data_col_index = self.sample_id_col_index + 1
        self.last_data_col_index = self.first_data_col_index + self._num_field_columns - 1

        # NB: This code asserts that the name column we want to look at is the FIRST data column (that is, separate from
        # the hidden, auto-filled sample_id column) in the metadata grid.  This is because the name
        # column being the first data column is in fact a REQUIREMENT from the customer; however, if that changed
        # sometime down the road, *this* is where that change should be reflected.
        self.name_col_index = self.first_data_col_index

        if make_sheet:
            self.worksheet = self._create_worksheet(self.metadata_sheet_name, self._permissive_protect_options,
                                                    num_cols_to_freeze=self.name_col_index + 1)

    def _create_worksheet(self, sheet_name, permissive_protect_options=None, num_cols_to_freeze=1):
        result = create_worksheet(self.workbook, sheet_name, permissive_protect_options, num_cols_to_freeze)

        first_unused_col_letter = get_col_letters(self.last_data_col_index+1)
        result.set_column('{0}:XFD'.format(first_unused_col_letter), None, None, {'hidden': True})
        result.set_default_row(hide_unused_rows=True)

        return result


# region functions for working with worksheet objects
def write_header(a_sheet, the_field_name, col_index, row_index=None):
    """

    :type a_sheet: ValidationWorksheet or MetadataWorksheet
    """
    row_index = row_index if row_index is not None else a_sheet.name_row_index
    the_col_letter = get_col_letters(col_index)
    a_sheet.worksheet.write("{0}{1}".format(the_col_letter, row_index), the_field_name, a_sheet.bold_format)


def format_single_col_range(val_sheet, col_index, sheet_name=None, first_col_fixed=False, first_row_fixed=False,
                            last_col_fixed=None, last_row_fixed=False):
    """

    :type val_sheet: ValidationWorksheet
    """
    return format_range(col_index, val_sheet.first_data_row_index,
                        last_row_index=val_sheet.last_data_row_index,
                        sheet_name=sheet_name,
                        first_col_fixed=first_col_fixed, first_row_fixed=first_row_fixed,
                        last_col_fixed=last_col_fixed, last_row_fixed=last_row_fixed)


def format_single_data_grid_row_range(val_sheet, row_index, sheet_name=None,
                                      first_col_fixed=False, first_row_fixed=False,
                                      last_col_fixed=None, last_row_fixed=False):
    """

    :type val_sheet: ValidationWorksheet or MetadataWorksheet
    """
    return format_range(val_sheet.first_data_col_index, row_index,
                        last_col_index=val_sheet.last_data_col_index,
                        sheet_name=sheet_name,
                        first_col_fixed=first_col_fixed, first_row_fixed=first_row_fixed,
                        last_col_fixed=last_col_fixed, last_row_fixed=last_row_fixed)


def format_single_static_grid_row_range(val_sheet, row_index, sheet_name=None,
                                        first_col_fixed=False, first_row_fixed=False,
                                        last_col_fixed=None, last_row_fixed=False):
    """

    :type val_sheet: ValidationWorksheet
    """
    return format_range(val_sheet.first_static_grid_col_index, row_index,
                        last_col_index=val_sheet.last_static_grid_col_index,
                        sheet_name=sheet_name,
                        first_col_fixed=first_col_fixed, first_row_fixed=first_row_fixed,
                        last_col_fixed=last_col_fixed, last_row_fixed=last_row_fixed)


def write_array_formula(val_sheet, range_index, array_formula_str, write_col, sheet_name=None,
                        first_col_fixed=False, first_row_fixed=False, last_col_fixed=None, last_row_fixed=False):
    """

    :type val_sheet: ValidationWorksheet
    """
    if write_col:
        range_builder_func = format_single_col_range
    else:
        range_builder_func = format_single_static_grid_row_range

    range_to_hold_formula = range_builder_func(val_sheet, range_index, sheet_name, first_col_fixed,
                                               first_row_fixed, last_col_fixed, last_row_fixed)
    val_sheet.worksheet.write_array_formula(range_to_hold_formula, array_formula_str)
    return range_to_hold_formula


# NB: Most of the time when I create a range for later use, I WANT it to be fixed, so the defaults of the fixed
# parameters for *this* function are all True (unlike in the other, lower-functions that take them).
def format_and_write_array_formula(val_sheet, array_formula_range_index, formula_string, write_col,
                                   cell_range_str=None, first_col_fixed=True, first_row_fixed=True,
                                   last_col_fixed=True, last_row_fixed=True):
    """
    :type val_sheet: ValidationWorksheet
    """
    if cell_range_str is not None:
        formula_string = formula_string.format(cell=cell_range_str)
    array_formula_str = "{=" + formula_string + "}"
    # None = sheet_name, since this method doesn't accept a sheet name
    range_to_hold_formula = write_array_formula(val_sheet, array_formula_range_index, array_formula_str, write_col,
                                                first_col_fixed=first_col_fixed, first_row_fixed=first_row_fixed,
                                                last_col_fixed=last_col_fixed, last_row_fixed=last_row_fixed)
    return range_to_hold_formula

# end region
