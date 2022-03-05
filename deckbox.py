import csv
from card_kingdom import Card_kingdom
import os
from bcolors import info_print
import requests
import json
import time

ck_fields = {
  'NAME': 'card name',
  'SET': 'edition',
  'FOIL': 'foil',
  'COUNT': 'quantity',
}

fields = {
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

def db_name_set_to_ck_name_set(old_name, old_set, card_number, set_info):
  if(old_set == 'Friday Night Magic'):
    return '%s (FNM FOIL)' % old_name, 'Promotional'
  if('Prerelease Events' in old_set):
    return '%s (Prerelease foil)' % old_name, 'Promotional'
  if(old_set == 'Welcome Deck 2016'):
    return '%s (Welcome 2016)' % old_name, 'Promotional'
  if(old_set == 'Zendikar Rising' and '//' in old_name):
    return old_name[:old_name.index(' // ')], old_set
  if(old_set == 'Launch Parties'):
    return '%s (Launch Foil)' % old_name, 'Promotional'
  if(old_set == 'Strixhaven: School of Mages' and '//' in old_name):
    return old_name[:old_name.index(' // ')], old_set
  return db_name_to_ck_name(old_name), db_set_to_ck_set(old_set, card_number, set_info)

def db_set_to_ck_set(old_set, card_number, set_info):
  abbr_set = None
  for set_data in set_info:
    set_name = set_data['name'].lower()
    if old_set.lower() == set_name:
      abbr_set = set_data['code']
      break

  if(not abbr_set):
    return old_set

  pricing_url = "https://api.scryfall.com/cards/collection"
  headers = {"Accept": "application/json", "Content-Type": "application/json"}
  # check price
  card_request_body = {"identifiers": []}
  card_request_body['identifiers'].append({
    "collector_number": card_number,
    "set": abbr_set,
  })
  card_data = requests.request("POST", pricing_url, headers=headers, json=card_request_body)
  if(card_data.status_code != 200):
      info_print('~~~~ Error while getting card data ~~~~~')
      info_print('Status code ** %d ** for card Card Number: %s, Set: %s' % (card_data.status_code, card_number, abbr_set))
      info_print('Response:\n%s\n\n' % card_data.text)
      return old_set
  card_data = json.loads(card_data.text)["data"][0] if json.loads(card_data.text)["data"] else []
  frame_data = card_data['frame_effects'] if 'frame_effects' in card_data else []
  if(frame_data):
    if('etched' in frame_data or 'extendedart' in frame_data or 'showcase' in frame_data):
      return '%s Variants' % old_set

  if(old_set == 'Amonkhet Invocations'):
    return 'Masterpiece Series: Invocations'
  if(old_set == 'Archenemy: Nicol Bolas'):
    return 'Archenemy - Nicol Bolas'
  if(old_set == 'Commander Anthology Volume Ii' or old_set == 'Commander Anthology Volume II'):
    return 'Commander Anthology Vol. II'
  if('Extras' in old_set):
    return ''
  if(old_set == 'Ravnica: City of Guilds'):
    return 'Ravnica'
  if(old_set == 'The List' or old_set == 'Myster Booster'):
    return 'Mystery Booster/The List'
  if(old_set == 'Zendikar Rising Commander'):
    return 'Zendikar Rising Commander Decks'
  if(old_set == 'Ravnica Allegiance Guild Kit'):
    return 'Ravnica Allegiance: Guild Kits'
  
  return old_set

def db_name_to_ck_name(old_name):
  if(old_name == 'Bow of the Hunter'):
    return ''
  if(old_name == 'Nexus of Fate'):
    return 'Nexus of Fate (Buy-a-Box Foil)'
  if(old_name == 'Impervious Greatwurm'):
    return 'Impervious Greatwurm (Buy-a-Box Foil)'
  if(old_name == 'Legions of Lim-Dûl'):
    return 'Legions of Lim-Dul'
  return old_name

class Deckbox:
  def __init__(self, csv_fields, csv_rows):
    self.csv_fields = csv_fields
    self.csv_rows = csv_rows
    sets_url = "https://api.scryfall.com/sets"
    headers = {"Accept": "application/json"}
    self.set_info = json.loads(requests.request("GET", sets_url, headers=headers).text)['data']

  def to_card_kingdom(self, row_limit, output_file_name='ck_massaged'):
    # ck_fields = Card_kingdom.fields
    # csvreader = csv.reader(self.csvfile)

    count_index = self.csv_fields.index(fields['COUNT'])
    foil_index = self.csv_fields.index(fields['FOIL'])
    name_index = self.csv_fields.index(fields['NAME'])
    set_index = self.csv_fields.index(fields['SET'])
    card_number_index = self.csv_fields.index('Card Number')

    new_rows = []
    new_rows.append(ck_fields.values())
    for index, row in enumerate(self.csv_rows):
      complete_percent = round(float((index/len(self.csv_rows)) * 100), 2)
      info_print("========  {:.2f}% complete massaging deckbox file  ========".format(complete_percent), "\r")

      if(len(row) <= 0):
        continue
      time.sleep(.2)
      card_name, card_set = db_name_set_to_ck_name_set(row[name_index], row[set_index], row[card_number_index], self.set_info)

      if(not card_name or not card_set):
        continue
      def get_full_output_file_name(is_paged):
        if(not is_paged and not os.path.exists('%s_ck_massaged.csv' % output_file_name)):
          return '%s_ck_massaged.csv' % output_file_name
        
        test_page = 0
        while(os.path.exists('%s_ck_massaged%d.csv' % (output_file_name, test_page))):
          test_page += 1
        return '%s_ck_massaged%d.csv' % (output_file_name, test_page)

      if(row_limit):
        if(len(new_rows) > row_limit):
          file_to_write = get_full_output_file_name(not not row_limit)
          with open(file_to_write, 'w') as csvfile_writer:
            csvwriter = csv.writer(csvfile_writer)
            csvwriter.writerows(new_rows)
            info_print('Successfully wrote %s' % file_to_write)
            
          new_rows = []
          new_rows.append(ck_fields.values())

      new_rows.append([
        card_name,
        card_set,
        'true' if row[foil_index] else 'false',
        row[count_index]
      ])

    full_file_name = get_full_output_file_name(not not row_limit)
    with open(full_file_name, 'w') as csvfile_writer:
      csvwriter = csv.writer(csvfile_writer)
      csvwriter.writerows(new_rows)
      info_print('Successfully wrote %s' % full_file_name)
    
    self.to_sell_rows = new_rows
    
    to_sell_ck = Card_kingdom()
    to_sell_ck.to_deckbox()

