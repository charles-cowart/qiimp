import xlsx_basics
import xlsx_validation_builder


def write_metadata_grid(data_worksheet, schema_dict):
    """

    :type data_worksheet: xlsx_basics.MetadataWorksheet
    """

    _write_sample_id_col(data_worksheet)

    unlocked = data_worksheet.workbook.add_format()
    unlocked.set_locked(False)

    sorted_keys = sorted(schema_dict.keys())
    for field_index, field_name in enumerate(sorted_keys):
        field_specs_dict = schema_dict[field_name]
        curr_col_index = field_index + 1  # add one bc sample id is in first col

        xlsx_basics.write_header(data_worksheet, field_name, field_index + 1)
        data_worksheet.worksheet.set_column(curr_col_index, curr_col_index, None, unlocked)

        starting_cell_name = xlsx_basics.format_range(curr_col_index, data_worksheet.first_data_row_index)
        whole_col_range = xlsx_basics.format_range(curr_col_index, data_worksheet.first_data_row_index,
                                                   second_row_index=data_worksheet.last_allowable_row_for_sample_index)

        validation_dict = _get_validation_dict(field_name, field_specs_dict)
        value_key = "value"
        if validation_dict is not None:
            if value_key in validation_dict:
                unformatted_validation_formula = validation_dict[value_key]
                formatted_validation_formula = unformatted_validation_formula.format(cell=starting_cell_name)
                validation_dict[value_key] = formatted_validation_formula

                data_worksheet.worksheet.data_validation(whole_col_range, validation_dict)

        _add_default_if_any(data_worksheet, field_specs_dict, curr_col_index)


def _write_sample_id_col(data_sheet):
    """

    :type data_sheet: xlsx_basics.MetadataWorksheet
    """

    data_sheet.worksheet.set_column(data_sheet.sample_id_col_index, data_sheet.sample_id_col_index, None, None,
                                    data_sheet.hidden_cell_setting)
    xlsx_basics.write_header(data_sheet, "sample_id", data_sheet.sample_id_col_index)

    # +1 bc range is exclusive of last number
    for row_index in range(data_sheet.first_data_row_index, data_sheet.last_allowable_row_for_sample_index + 1):
        curr_cell = xlsx_basics.format_range(data_sheet.sample_id_col_index, row_index)
        id_num = row_index - data_sheet.first_data_row_index + 1
        data_row_range = xlsx_basics.format_single_data_grid_row_range(data_sheet, row_index)

        completed_formula = "=IF(COUNTBLANK({data_row_range})<>COLUMNS({data_row_range}),{id_num},\"\")".format(
            data_row_range=data_row_range, id_num=id_num)
        data_sheet.worksheet.write_formula(curr_cell, completed_formula)


def _get_validation_dict(field_name, field_schema_dict):
    result = None
    validation_generators = [
        _make_allowed_only_constraint,
        _make_formula_constraint
    ]

    for curr_generator in validation_generators:
        curr_validation_dict = curr_generator(field_name, field_schema_dict)
        if curr_validation_dict is not None:
            result = curr_validation_dict
            break
        # end if validation generated
    # next validation generator

    return result


def _make_allowed_only_constraint(field_name, field_schema_dict):
    result = None
    allowed_onlies = xlsx_validation_builder.roll_up_allowed_onlies(field_schema_dict)

    if allowed_onlies is not None and len(allowed_onlies) > 0:
        allowed_onlies_as_strs = [str(x) for x in allowed_onlies]
        result = {'validate': 'list', 'source': allowed_onlies,
                  'input_title': 'Enter {0}:'.format(field_name),
                  'input_message': '{0} must be one of these allowed values: {1}'.format(
                      field_name, ", ".join(allowed_onlies_as_strs))
                  }
    return result


def _make_formula_constraint(field_name, field_schema_dict):
    result = None
    formula_string = xlsx_validation_builder.get_formula_constraint(field_schema_dict)

    if formula_string is not None:
        formula_string = "=("+formula_string + ")"
        result = {
            'validate': 'custom', 'value': formula_string,
            'input_title': 'Enter {0}:'.format(field_name),
            'input_message': 'placeholder'
        }
    return result


def _add_default_if_any(data_worksheet, field_specs_dict, col_index):
    """

    :type data_worksheet: xlsx_basics.MetadataWorksheet
    """

    # So, you might be thinking: why don't we look at the sample_id column rather than the first visible metadata column
    # to determine if the user has entered anything for this sample?  After all, the sample_id is filled if ANY
    # column has something in it. Yes, but therein lies the problem: the sample_id is filled if there is anything in
    # the first visible metadata column (among others), so it *depends on* every visible metadata column--which means
    # that if the first visible metadata column in turn depends on the sample_id column, then we have a circular
    # reference.  Filling defaults only when the first visible metadata column is filled is not ideal, but should still
    # serve the need since the first visible column is a sensible place for people to start filling things in and
    # b) Austin says that anonymized_name, which will be always be required for every sample, is supposed to be the
    # first column always.

    trigger_col_range_str = xlsx_basics.format_range(data_worksheet.first_data_col_index,
                                                     data_worksheet.first_data_row_index,
                                                     second_row_index=data_worksheet.last_allowable_row_for_sample_index)
    default_formula = xlsx_validation_builder.get_default_formula(field_specs_dict, trigger_col_range_str)
    if default_formula is not None:
        xlsx_basics.format_and_write_array_formula(data_worksheet, col_index, default_formula, write_col=True)
