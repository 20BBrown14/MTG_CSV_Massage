# Library imports
from os import listdir, remove, path
from os.path import isfile, join
from math import ceil
import csv

# Local imports
from bcolors import color_print, warning_print, error_print, info_print, success_print, instruction_print, color_input, colors
import csv_formats
from Deckbox import Deckbox

INPUT_FILE_DIRECTORY_NAME = './input_csv_files'
OUTPUT_FILE_DIRECTORY_NAME = './output_csv_files'

SUPPORTED_INPUT_CSV_FORMATS = ['Deckbox', 'Card Kingdom']
SUPPORTED_OUTPUT_CSV_FORMATS = ['Deckbox', 'Card Kingdom']

# All input files for this session
global all_input_files
all_input_files = []

# Main input csv file
global main_input_file
main_input_file = ''

global exclusion_files
exclusion_files = []

# Determine if file is csv
# param file: string containg file name
def file_is_csv(file):
  return file.endswith('.csv')

# Get files in given directory
# Filters out non-csv files
# Sorts alphabetically
# Sets all_input_files global var
# param directory: string directory
def get_files_in_directory(directory):
  global all_input_files
  if(directory == INPUT_FILE_DIRECTORY_NAME):
    if (len(all_input_files) > 0):
      return all_input_files
  files = sorted([file for file in listdir(directory) if isfile(join(directory, file))])
  if(directory == INPUT_FILE_DIRECTORY_NAME):
    filtered_files = list(filter(file_is_csv, files))
    if(filtered_files != files):
      info_print('Ignoring non .csv files')
      files = filtered_files
    all_input_files = files
  return files

# Deletes array of files inside of relative ./output_csv_files directory
# param files_to_delete: array of strings container file names
def delete_files(files_to_delete):
  print('Deleting files %s' % files_to_delete)
  for file in files_to_delete:
    file_name = '%s/%s' % (OUTPUT_FILE_DIRECTORY_NAME, file)
    try:
      if path.exists(file_name):
        remove(file_name)
      else:
        info_print('%s does not exist' % file)
    except Exception as e:
      warning_print('Could not remove %s' % file)
      print(e)

# Determines if the output directory should be cleraed
def clear_output_directory():
  should_clear_output_files = ''
  output_dir_files = get_files_in_directory(OUTPUT_FILE_DIRECTORY_NAME)
  if len(output_dir_files) > 0:
    should_clear_output_files = input('Would you like to clear the output directory? [y/N]: ')
  if should_clear_output_files == 'y':
    delete_files(output_dir_files)

# Paginates a dict with 10 per page
def paginate_dict(dict_to_paginate):
  page_count = ceil(len(dict_to_paginate) / 10)
  pages = []

  for page in range(1, page_count + 1):
    current_range_bottom = (page - 1) * 10
    current_range_top = len(dict_to_paginate) if page * 10 > len(dict_to_paginate) else page * 10

    current_range = range(current_range_bottom, current_range_top)

    pages.append([{index: dict_to_paginate.get(index)} for index in current_range])
  
  return pages

# Get input for a paginated source
def get_paginated_input(pages):
  selection = ''
  current_page = 0

  while not selection:
    current_index = 0
    for value in pages[current_page]:
      print('%s: %s' % (current_index, list(value.values())[0]))
      current_index += 1
    user_input = color_input('Select a file. "n" for next page, "p" for previous page:')

    if(user_input == 'p'):
      current_page -= 1
      if(current_page < 0):
        current_page = 0
    elif(user_input == 'n'):
      current_page += 1
      if(current_page >= len(pages)):
        current_page -= 1
    elif(not user_input):
      return selection
    elif(user_input.isnumeric() and int(user_input) >= 0 and int(user_input) < 10):
      selection = list(pages[current_page][int(user_input)].values())[0]
  
  return selection  

# Determines the input files including main source and exclusions
# Sets global var main_input_file
# param has_exclusions: Whether there are files with exclusions
def get_input_files(has_exclusions):
  global main_input_file

  input_files = get_files_in_directory(INPUT_FILE_DIRECTORY_NAME)
  indexed_input_files = dict((input_files.index(file), file) for file in input_files)
  output_pages = paginate_dict(indexed_input_files)

  while(not main_input_file):
    instruction_print('Please select the main input file')
    main_input_file = '%s' % get_paginated_input(output_pages)
    if(not main_input_file):
      warning_print('Main input file cannot be empty')

  more_exclusions = True

  while(has_exclusions and more_exclusions):
    instruction_print('Please select the file that includes exclusions')
    excluded_file = get_paginated_input(output_pages)
    if(excluded_file):
      if(not excluded_file in exclusion_files):
        exclusion_files.append('%s/%s' % (INPUT_FILE_DIRECTORY_NAME, excluded_file))
        continue
      warning_print('%s has already been selected' % excluded_file)
      info_print('Excluded files selected thus far: %s' % exclusion_files)
    else:
      more_exclusions = False

  info_print('Main input file selected: %s/%s' % (INPUT_FILE_DIRECTORY_NAME, main_input_file))
  info_print('Files that include exclusions: %s' % exclusion_files)

# Asks user if they have files that are excluded
def have_files_that_include_exclusions():
  return color_input('Do you have files that include exclusions? [y/N]:') == 'y'

def should_split_file():
  if(color_input('Should the file be split into smaller pieces? [Y/n]') == 'n'):
    return False
  return color_input('Rows per file (Default 450):') or 450

def main():
  instruction_print("Welcome to the MTG_CSV_Massager")
  clear_output_directory()
  have_exclusions = have_files_that_include_exclusions()
  get_input_files(have_exclusions)
  row_limit = should_split_file()

  with open('%s/%s' % (INPUT_FILE_DIRECTORY_NAME, main_input_file), 'r') as csvfile:
    deckbox = Deckbox(csvfile)
    deckbox.to_card_kingdom(row_limit, '%s/%s' % (OUTPUT_FILE_DIRECTORY_NAME, main_input_file))

if __name__ == '__main__':
  main()