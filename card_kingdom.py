import csv
import json
import requests

fields = {
  'NAME': 'card name',
  'SET': 'edition',
  'FOIL': 'foil',
  'COUNT': 'quantity',
}

db_fields = {
  'ALTERED_ART': 'Altered Art',
  'ARTIST_PROOF': 'Artist Proof',
  'CARD_NUMBER': 'Card Number',
  'CONDITION': 'Condition',
  'COST': 'Cost',
  'COUNT': 'Count',
  'FOIL': 'Foil',
  'IMAGE_URL': 'Image URL',
  'LANGUAGE': 'Language',
  'LAST_UPDATED': 'Last Updated',
  'MISPRINT': 'Misprint',
  'NAME': 'Name',
  'PRICE': 'Price',
  'RARITY': 'Rarity',
  'SECTION': 'Section',
  'SET': 'Edition',
  'SIGNED': 'Signed',
  'TYPE': 'Type'
}

class Card_kingdom:
  def __init__(self, csv_file_name="input_csv_files/to_sell.csv"):
    self.csv_file_name = csv_file_name

  def to_deckbox(self, output_file_name="output_csv_files/to_sell.txt"):
    sets_url = "https://api.scryfall.com/sets"
    headers = {"Accept": "application/json"}
    set_info = json.loads(requests.request("GET", sets_url, headers=headers).text)['data']

    count_index = 3
    name_index = 0
    edition_index = 1

    with open(self.csv_file_name, 'r') as csvfile:
      csv_reader = csv.reader(csvfile)
      csv_fields = next(csv_reader)

      new_rows = []
      # new_rows.append(['Count', 'Name', 'Edition'])
      
      for row in csv_reader:
        if(len(row) <= 0):
          continue
        card_set = row[edition_index].lower()

        for set_data in set_info:
          set_name = set_data['name'].lower()
          if(card_set == set_name):
            new_row = [
              row[count_index],
              row[name_index],
              '(%s)' % set_data['code'],
            ]
            new_rows.append(' '.join(new_row))

    f = open(output_file_name, 'w')
    for row_to_write in new_rows:
      f.write(row_to_write)
      f.write('\n')
    f.close()


