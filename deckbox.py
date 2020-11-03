import csv
import Card_kingdom
import os
from bcolors import info_print

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

def db_name_set_to_ck_name_set(old_name, old_set):
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
  return db_name_to_ck_name(old_name), db_set_to_ck_set(old_set)

def db_set_to_ck_set(old_set):
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

  def to_card_kingdom(self, row_limit, output_file_name='ck_massaged'):
    ck_fields = Card_kingdom.fields
    # csvreader = csv.reader(self.csvfile)

    count_index = self.csv_fields.index(fields['COUNT'])
    foil_index = self.csv_fields.index(fields['FOIL'])
    name_index = self.csv_fields.index(fields['NAME'])
    set_index = self.csv_fields.index(fields['SET'])

    new_rows = []
    new_rows.append(ck_fields.values())
    for row in self.csv_rows:
      if(len(row) <= 0):
        continue
      card_name, card_set = db_name_set_to_ck_name_set(row[name_index], row[set_index])

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

