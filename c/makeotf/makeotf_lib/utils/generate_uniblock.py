"""
Copyright 2019 Adobe
All Rights Reserved.

This software is licensed as OpenSource, under the Apache License, Version 2.0.
This license is available at: http://opensource.org/licenses/Apache-2.0.

--------------------------------------------------------------------------------

This script converts OS/2 Unicode ranges from:
https://docs.microsoft.com/en-us/typography/opentype/spec/os2#ur
(save this section of the page as "os2_ur.txt")

...and Unicode data from:
https://unicode.org/Public/UNIDATA/UnicodeData.txt
(save this file as "UnicodeData.txt")

...into uniblock.h for use in makeotf.
"""
import csv


def _count_chars_in_range(unichars, start, end):
    count = 0
    for unichar in range(start, end + 1):
        if unichar in unichars:
            count += 1
    return count


def _fix_title_casing(name):
    conjunctions = ['And', 'For']
    for conjunction in conjunctions:
        conj_with_spaces = ' ' + conjunction + ' '
        if conj_with_spaces in name:
            name = name.replace(conj_with_spaces, conj_with_spaces.lower())
    return name


def _print_header():
    print(
        '/*\n'
        '   Copyright 2014 Adobe\n'
        '   All Rights Reserved.\n'
        '   This software is licensed as OpenSource, under the Apache License,'
        ' Version 2.0.\n'
        '   This license is available at: '
        'http://opensource.org/licenses/Apache-2.0.\n'
        '*/\n'
        '\n'
        '/*\n'
        '   DO NOT EDIT: this file was generated by the Python script '
        'generate_uniblock.py.\n'
        '   ( c/makeotf/makeotf_lib/utils/generate_uniblock.py )\n'
        '\n'
        '   Unicode block information (struct type: UnicodeBlock). Ordered by '
        'first\n'
        '   Unicode value in range. Ranges do not overlap. '
        'Bit 57 "Non-Plane 0" is \n'
        '   handled separately in map.c (search on SUPP_UV_BITNUM).\n'
        '*/\n'
    )


def _get_unichars():
    unichars = set()
    with open('UnicodeData.txt') as unicodedata_file:
        reader = csv.reader(unicodedata_file, delimiter=';')
        start = None
        for row in reader:
            unichar = int(row[0], 16)
            name = row[1]
            if 'First' in name:
                start = unichar
            elif 'Last' in name:
                for char_in_range in range(start, unichar + 1):
                    unichars.add(char_in_range)
                start = None
            else:
                unichars.add(unichar)
    return unichars


def _get_os2_ur_records():
    # we want to set the corresponding OS/2 Unicode range bits
    # if we see *any* character in a PUA or CJK block
    bits_to_flag_on_any_char = {28, 48, 52, 54, 55, 56, 59, 60, 61, 65, 90}

    unichars = _get_unichars()
    records = list()
    prev_os2_num = 0
    with open('os2_ur.txt') as input_file:
        reader = csv.reader(input_file, delimiter='\t')
        for row in reader:
            if not row[0][0].isdigit():
                row.insert(0, prev_os2_num)
            if row[0] == '123-127':  # reserved stuff at end
                continue
            (os2_num, name, start_end, _) = row
            os2_num = int(os2_num)
            (start, end) = (int(x, 16) for x in start_end.split('-'))
            if os2_num == 57:  # 'Non-Plane 0'
                continue  # this is handled in map.c, search on SUPP_UV_BITNUM
            if os2_num in bits_to_flag_on_any_char:
                count = 1  # we want to flag on *any* characters in this block
            else:
                count = _count_chars_in_range(unichars, start, end)
            name = _fix_title_casing(name)
            record = (start, end, count, os2_num, name)
            records.append(record)
            prev_os2_num = os2_num
    return records


def _print_records(records):
    for record in sorted(records):
        (start, end, count, os2_num, name) = record
        start_str = '0x%04X' % start
        end_str = '0x%04X' % end
        name_str = '"%s"' % name
        print('    { %8s, %8s, %5d, %d, %3d, %d, %-41s },'
              % (start_str, end_str, count, 0, os2_num, 0, name_str))


def _main():
    _print_header()
    records = _get_os2_ur_records()
    _print_records(records)


if __name__ == '__main__':
    _main()
