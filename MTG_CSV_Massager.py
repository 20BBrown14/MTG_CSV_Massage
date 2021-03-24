# Library imports
from os import listdir, remove, path
from os.path import isfile, join
from math import ceil
import csv
import requests
import json
import time

# Local imports
from bcolors import color_print, warning_print, error_print, info_print, success_print, instruction_print, color_input, colors
import csv_formats
from deckbox import Deckbox

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

global minimum_value
minimum_value = None

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
    should_clear_output_files = color_input('Would you like to clear the output directory? [y/N]: ')
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

def get_value_minimum():
  global minimum_value

  if(color_input('Should value be searched? [Y/n]') == 'n'):
    minimum_value = -1
  while(not minimum_value):
    try:
      user_input = color_input('What minimum value should be searched for? (Default $1.00)')
      if(user_input == ''):
        minimum_value = 1.00
        continue
      
      minimum_value = float(user_input)
    except:
      minimum_value = None
  
def get_should_massage_file():
  if(color_input('Should the file be massaged to Card Kingdom format? [Y/n]') == 'n'):
    return False

  return True

def filter_exclusions(main_csv_file):
  fields_to_include = [
    'Count',
    'Name',
    'Edition',
    'Card Number',
    'Condition',
    'Language',
    'Foil',
    'Price',
  ]

  field_indexes = []

  main_csv_reader = csv.reader(main_csv_file)
  csv_fields = next(main_csv_reader)

  main_csv_rows = []

  for field in fields_to_include:
    field_indexes.append(csv_fields.index(field))

  for row in main_csv_reader:
    if (not len(row)):
      continue
    main_csv_row = []
    for field_index in field_indexes:
      main_csv_row.append(row[field_index])
    main_csv_rows.append(main_csv_row)

  if (not len(exclusion_files)):
    return fields_to_include, main_csv_rows

  rows_to_exclude = []
  for exclusion_file in exclusion_files:
    with open(exclusion_file, 'r') as csvfile:
      exclusion_file_reader = csv.reader(csvfile)
      exclusion_fields = next(exclusion_file_reader)
      for included_field in fields_to_include:
        if (not included_field in exclusion_fields):
          error_print('Exclusion file %s does not include all fields of main input CSV file. Exitting.' % exclusion_file)
          exit('1')

      for row in exclusion_file_reader:
        if (not len(row)):
          continue
        row_to_exclude = []
        for field in fields_to_include:
          row_to_exclude.append(row[exclusion_fields.index(field)])
        rows_to_exclude.append(row_to_exclude)

  filtered_csv_rows = []

  for excluded_row in rows_to_exclude:
    for index, main_row in enumerate(main_csv_rows):
      if (
        excluded_row[1] == main_row[1] and
        excluded_row[2] == main_row[2] and
        excluded_row[3] == main_row[3] and
        excluded_row[4] == main_row[4] and
        excluded_row[5] == main_row[5] and
        excluded_row[6] == main_row[6]):
        main_csv_rows[index][0] = str(int(main_csv_rows[index][0]) - int(excluded_row[0]))

  for main_row in main_csv_rows:
    if(int(main_row[0]) > 0):
      filtered_csv_rows.append(main_row)        

  return fields_to_include, filtered_csv_rows 

def search_for_value(csv_fields, filtered_card_data):
  sets_url = "https://api.scryfall.com/sets"
  headers = {"Accept": "application/json"}
  set_info = json.loads(requests.request("GET", sets_url, headers=headers).text)['data']

  cards_to_price = []
  value_card_data = [['Count', 'Name', 'Edition', 'Mana Cost', 'Rarity', 'Foil', 'Card Number', 'Price']]
  cards_with_no_data = [['Count', 'Name', 'Edition', 'Mana Cost', 'Rarity', 'Foil', 'Card Number', 'Price']]

  count_index = csv_fields.index('Count')
  name_index = csv_fields.index('Name')
  set_index = csv_fields.index('Edition')
  foil_index = csv_fields.index('Foil')
  card_number_index = csv_fields.index('Card Number')

  def price_cards():
    pricing_url = "https://api.scryfall.com/cards/collection"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    # check price
    price_request_body = {"identifiers": []}
    for card_to_price in cards_to_price:
      price_request_body['identifiers'].append({
        "collector_number": card_to_price[4],
        "set": card_to_price[2],
      })
    time.sleep(1)
    card_data = requests.request("POST", pricing_url, headers=headers, json=price_request_body)
    if(card_data.status_code != 200):
      info_print(card_data.json())
      return
    card_data = json.loads(card_data.text)["data"] if json.loads(card_data.text)["data"] else []
    for price in card_data:
      is_card_foil = False
      for card in cards_to_price:
        if(card[1] == price["name"] and card[2] == price["set"] and card[4] == price["collector_number"]):
          is_card_foil = card[3]
          card_price = price["prices"]["usd_foil"] if is_card_foil else price["prices"]["usd"]
          if(card_price == None):
            cards_with_no_data.append([
              card[0],
              card[1],
              price["set_name"] or "SET NOT AVAILABLE",
              price["mana_cost"] if "mana_cost" in price.keys() else ("%s // %s" % (price["card_faces"][0]["mana_cost"] or 'NO COST', price["card_faces"][1]["mana_cost"] or 'NO COST')) if price["card_faces"] else "COST NOT AVAILABLE",
              price["rarity"] or "RARITY NOT AVAILABLE",
              is_card_foil,
              card[4],
              card_price or 'PRICE NOT AVAILABLE',
            ])
          if(card_price and float(card_price) > minimum_value):
            value_card_data.append([
              card[0],
              card[1],
              price["set_name"],
              price["mana_cost"] if "mana_cost" in price.keys() else "%s // %s" % (price["card_faces"][0]["mana_cost"] or 'NO COST', price["card_faces"][1]["mana_cost"] or 'NO COST'),
              price["rarity"],
              is_card_foil,
              card[4],
              card_price,
            ])
          cards_to_price.remove(card)
          break
    # cards_to_price = []
  for index, row in enumerate(filtered_card_data):
    complete_percent = round(float((index/len(filtered_card_data)) * 100), 2)
    info_print("========  {:.2f}% complete getting card value  ========".format(complete_percent), "\r")
    if(len(cards_to_price) >= 70):
      price_cards()
      cards_to_price = []
    else:
      card_set = row[set_index].lower()
      for set_data in set_info:
        set_name = set_data['name'].lower()
        if card_set == set_name:
          cards_to_price.append([
            row[count_index],
            row[name_index],
            set_data['code'],
            row[foil_index],
            row[card_number_index]
          ])
          break
  
  if(len(cards_to_price) > 0):
    price_cards()
    cards_to_price = []
  if(len(value_card_data) > 0):
    with open('%s/value_output.csv' % OUTPUT_FILE_DIRECTORY_NAME, 'w') as csvfile_writer:
        csvwriter = csv.writer(csvfile_writer)
        csvwriter.writerows(value_card_data)
        info_print('Successfully wrote %s' % '%s/value_output.csv' % OUTPUT_FILE_DIRECTORY_NAME)  

    

def main():
  instruction_print("Welcome to the MTG_CSV_Massager")
  clear_output_directory()
  have_exclusions = have_files_that_include_exclusions()
  get_input_files(have_exclusions)
  row_limit = should_split_file()
  get_value_minimum()
  should_massage = get_should_massage_file()

  with open('%s/%s' % (INPUT_FILE_DIRECTORY_NAME, main_input_file), 'r') as csvfile:
    csv_fields, filtered_csv_rows = filter_exclusions(csvfile)
    if(not minimum_value == -1):
      search_for_value(csv_fields, filtered_csv_rows)
    if(should_massage):
      deckbox = Deckbox(csv_fields, filtered_csv_rows)
      deckbox.to_card_kingdom(row_limit, '%s/%s' % (OUTPUT_FILE_DIRECTORY_NAME, main_input_file))

  success_print('Run Complete!')

if __name__ == '__main__':
  main()