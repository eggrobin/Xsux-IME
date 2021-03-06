﻿import codecs
import csv
import re
import sys
import unicodedata

import numbers

sys.stdout = codecs.getwriter("utf-16")(sys.stdout.detach())

SOURCES = ['MesZL', 'Labat', 'ABZ']

def is_printable_basic_latin(c):
  return c >= "!" and c <= "~"

def is_lowercase_akkadian_letter(c):
  return c in 'bdgptkʾṭqzšsṣḫmnrlwyjaeiu'

def is_capital_akkadian_letter(c):
  return c in 'bdgptkʾṭqzšsṣḫmnrlwyjaeiu'.upper()

def is_digit(c):
  return c >= '0' and c <= '9'

def is_composition_sign(c):
  return c in 'f:⫶/v'

def is_composition_character(c):
  return (is_lowercase_akkadian_letter(c) or
          is_digit(c) or
          is_composition_sign(c) or
          c == 'x')

class Reading:
  def __init__(self, sign, šašková_index):
    self.value = ''
    self.comment = ''
    self.source = ''
    self.disambiguator = ''
    self.sign = sign
    self.šašková_index = šašková_index
    self.keep = True

  def composition(self):
    return self.value.lower() + self.disambiguator

  def normalize(self):
    # Properly write aleph, Y is a synonym for J, and we handle variant more
    # comprehensively than the single KAMᵛ.
    self.value = self.value.strip().replace(
        '’', 'ʾ').replace('Y', 'J').replace('v', '')
    self.comment = self.comment.replace('’', 'ʾ')
    source = re.match('^(\w+)[;:]', self.comment)
    if source:
      source = source[1]
      if source == 'KŠ':
        # Kateřina Šašková marks her own comments like this.
        # Since we are processing her list, everything is by definition therein;
        # the source field tracks provenance from older lists.
        return
      if source in ('MesZ', 'MeZL', 'MeLZ', 'MesLZ'):  # Typos.
        source = 'MesZL'
      if source not in SOURCES:
        raise ValueError('Unexpected source %s' % source)
      self.source = source

# See the comments below re. DUN₃ 𒂅, DUN₃ gunû 𒂆, and DUN₃ gunû gunû 𒂇.
DUN3_VARIANTS = {
  # http://oracc.museum.upenn.edu/ogsl/signlist/l0068/o0000160/index.html
  'DU5': '𒂅',
  'DUG5': '𒂅',
  'DUN3': '𒂅',
  'SU18': '𒂅',
  'SUG5': '𒂅',
  'TU18': '𒂅',
  'TUN3': '𒂅',
  'TUG8': '𒂅',
  'ṬU': '𒂅',
  # In Borger, not in Oracc.  Adding it where the SUG reading is.
  'SUK5': '𒂅',
  # Labat-only readings, not in Oracc; adding those to the variant with the
  # DUN/TUN and SU readings.
  'SU14': '𒂅',
  'ṬUN': '𒂅',
  # http://oracc.museum.upenn.edu/ogsl/signlist/l0068/o0000161/index.html
  'AGA3': '𒂆',
  'GE11': '𒂆',
  'GI11': '𒂆',
  'GIG4': '𒂆',
  'GIM2': '𒂆',
  'GIN2': '𒂆',
  'PUŠ4': '𒂆',
  # http://oracc.museum.upenn.edu/ogsl/signlist/l0080/o0002178/index.html
  'ḪURSAG': '𒂅',
  # http://oracc.museum.upenn.edu/ogsl/signlist/l0071/o0001279/index.html
  'AGARIN3': '𒂆',
  # http://oracc.museum.upenn.edu/ogsl/signlist/l0071/o0001367/index.html
  'GILGAMEŠ': '𒂆',
  'GILGAMES': '𒂆',
  # http://oracc.museum.upenn.edu/ogsl/signlist/l0090/o0002642/index.html
  'NIR2': '𒂆',
  # Labat-only reading, not in Oracc.
  'NINI2': '𒂆',
}

readings_by_value = {}
readings_by_sign = {}

def insert_parentheses(original, amendment):
  original_segment = amendment.replace('[', '').replace(']', '')
  amended_segment = amendment.replace('[', '(').replace(']', ')')
  return original.replace(original_segment, amended_segment)

def delete_parentheses(original, amendment):
  original_segment = amendment.replace('[', '(').replace(']', ')')
  amended_segment = amendment.replace('[', '').replace(']', '')
  return original.replace(original_segment, amended_segment)

with open(r".\sign_list.csv", encoding="utf-8") as file:
  reader = csv.reader(file)
  ok_entries = 0
  erroneous_entries = 0
  meszl_seen = {}

  row_index = 0

  for row in reader:
    meszl = row[3]
    if meszl in meszl_seen:
      meszl_seen[meszl] += 1
      meszl += '/%d' % meszl_seen[meszl]
    else:
      meszl_seen[meszl] = 1

    if (not row[0] or
        any(is_printable_basic_latin(c) for c in row[0] + row[1]) or
        row[0] != row[1]):
      if meszl == '003+003\n(839+756+003+003)':
        # A spelling of Idiqlat in the MesZL glossary.  No sign name, just type
        # it as ḪAL.ḪAL.
        continue
      elif row[2].startswith('UŠUMX\n'):
        pass  # UŠUMₓ is missing in the Sinacherib font.
      elif row[2].startswith('ARAD x ŠE\n'):
        continue  # Labat has ìr×še but Borger does not; it is not encoded.
      elif (row[0] and all(not is_printable_basic_latin(c) for c in row[0]) and
            (not row[1] or
             (any(is_printable_basic_latin(c) for c in row[1]) and
              (all (word.strip() in ('', '.', 'x', 'over', 'inverted', 'crossing',
                                     'opposing',)
               for word in re.split('[^!-~]', row[1])))))):
        pass  # Signs missing in the Sinacherib font.
      elif '𒄒' in row[0] and row[1] == row[0].replace('𒄒', '𒁉𒑖'):
        # The Sinacherib font has a GIŠ crossing GIŠ which does not look like
        # the neo-Assyrian KIB; these should be unified, and a neo-Assyrian font
        # should have the KIB glyph for that code point.
        pass
      elif meszl == '58':
        continue  # 𒅗×𒌍 is an unencoded variant of 𒅗×𒊓 = 𒅾.
      elif meszl in (
          '27',
          '36',  # HZL 137: unbekannte Bedeutung (Gegenstand aus Holz).
          '40',  # HZL 138: Gerät?, Behälter? aus Kupfer.
          '41',  # HZL 139: ein Behälter aus Holz.
          '55',
          '67',  # HZL 150: Körperteilbezeichnung?
          '70',  # HZL 142: u.B.
          '156',
          '194',
          '224',
          '243',
          '278',
          '282',
          '319/2',
          '322',
          '393',
          '408/2',
          '454',
          '488',
          '518',
          '524',
          '647',
          '680',
          '697',
          '763',
          '886',
        ):
        # Signs from https://www.unicode.org/wg2/docs/n4277.pdf.
        pass
      elif 'BAD squared' in row[2]:
        # We unify BAD squared with IDIM over IDIM squared, since IDIM is part
        # of BAD in both Labat and Borger, and both sign lists mention only a
        # squared BAD, not a squared IDIM over IDIM; indeed the latter has no
        # reading in Šašková.
        pass
      elif row[2].startswith('NUN crossing NUN.LAGAR over LAGAR'):
        continue  # Unified with TUR3 over TUR3, we keep the one with readings.
      elif row[2].startswith('TUR3 over TUR3\n'):
        pass  # See above.
      elif row[2].startswith('ŠIR over ŠIR.BUR over BUR'):
        pass  # Sign missing in the Sinacherib font.
      elif ('𒊩𒌆' in row[0] and
            row[0] in row[1] and
            row[0].replace('𒊩𒌆', '𒊩𒈠') in row[1]
            and 'Neo-Assyrian:' in row[1]):
        # Prior to the encoding of NIN one had to use either MUNUS.TUG₂ or
        # MUNUS.MA, the latter being the neo-Assyrian style.  Šašková gives
        # both, with a note.
        pass
      elif meszl == '170 (also 250)':
        # Borger lists two variant glyphs of TA×ḪI as separate entries, the
        # second one being only a reference to the former.  Only one is
        # encoded.
        pass
      elif meszl == '250':
        continue  # That one is a reference without readings in Šašková.
      elif meszl == '250 (also 170)':
        # Same as '170 (also 250)', except there is one more reading.
        pass
      elif row[2].startswith('SA.NI'):
        pass # Labat-only sign, no neo-Assyrian form.
      elif meszl == '177':
        # Borger writes USAN (GÚ×NUN, GÚ-NUN), and thus Šašková gives both
        # 𒄛 and 𒄘𒉣.  On the other hand for 178, Borger writes
        # DUR (GÚ×GAG, GÚ-GAG) yet Šašková gives only 𒄙 and lets the
        # neo-Assyrian font handle it by rendering that as GÚ-GAG.  Leave the
        # variant of USAN up to the font here too; Borger gives only one
        # Assyrian glyph anyway.
        pass
      elif meszl == '189':
        # As far as I can tell 𒊕×𒉌 SAG×NI is not encoded.  It is attested,
        # e.g., https://cdli.ucla.edu/search/archival_view.php?ObjectID=P217023.
        # Its reading is unknown.  It probably should be encoded.
        continue
      elif meszl in ('231', '231/2'):
        # Same story for 𒀊×𒌋 AB×U, attested, e.g., in
        # https://cdli.ucla.edu/search/archival_view.php?ObjectID=P227527.
        # Unclear whether AB×AŠ is actually a thing; both are under 231.
        continue
      elif meszl == '233':
        # Similarly for 𒀊×𒆠 AB×KI, but if I am reading Borger correctly that
        # one is only attested in one or two tablets (MSL 16 218 211, whatever
        # that means exactly).  Nothing on CDLI.
        continue
      elif meszl == '208':
        # As far as I can tell NIQ₃ is not encoded; is it even a thing? It comes
        # with a great deal of question marks in the litterature.
        continue
      elif meszl in ('240', '240/2'):
        # UM×U-LAGAB, URUDU×U-LAGAB, not encoded.
        continue
      elif row[2].startswith('URUDU x U'):
        # Unencoded variant of UM×U, same number in Borger.
        continue
      elif row[2].startswith('DUB x ŠA3'):
        # DUB×ŠA₃ is not encoded, UM×ŠA₃ is.  The latter reading is also
        # mentioned as Landsberger’s in Borger’s entry 244.  Šašková writes “old
        # variant of DUB x ŠA3?” in her entry for UM×ŠA₃; just unify them.
        pass
      elif row[2].startswith('DUB x LAGAB'):
        # Exact same story with DUB×LAGAB vs. UM×LAGAB, 245.
        pass
      elif meszl == '254':
        # KAM₂ has the same neo-Assyrian glyph as GAN (253).  In Labat (143),
        # the Babylonian glyph is shown as a tilted version of that neo-Assyrian
        # glyph.  That tilted glyph also appears in Borger as KAMᵛ, in the entry
        # 595 for KAM, and in the middle Assyrian section of Labat’s entry 406
        # for KAM.  Borger gives no Babylonian glyph for KAM₂, so it is possible
        # that he calls any tilted GAN KAMᵛ.
        # Unicode has U+1219A (KAM2) 𒆚 whose reference glyph is tilted.
        # This would match the Babylonian glyphs for KAM₂, or the glyph KAMᵛ.
        # Šašková’s list exclaims that KAM2 is the wrong name for that
        # character, i.e., that it represents KAMᵛ.  There isn’t much intrinsic
        # to the standard that implies that: the reference glyphs are
        # Babylonian,.so KAM₂ would have this glyph, and KAMᵛ would be an
        # unencoded variant.  It is unclear whether KAMᵛ is a thing outside of
        # Assyrian styles, so it may well be that it need not be encoded by the
        # standards of Unicode.
        # Indeed KAM appears to be a common transcription of KAMᵛ, and KAM
        # written 𒄭×𒁁 seems rare in neo-Assyrian.
        # Where Šašková goes with
        # 𒄰 = ḪI×BAD = KAM ≠ KAMᵛ = U+1219A 𒆚, KAM₂ = GAN or unencoded,
        # we choose
        # 𒄰 = ḪI×BAD = KAM = KAMᵛ ≠ KAM₂ = U+1219A 𒆚 KAM2 ≠ GAN.
        # This approach is etymologically sound. It also has the advantage of
        # being consistent with Oracc conventions, which, being maintained under
        # the auspices of Tinney who co-authored the Unicode proposals, are
        # probably sound.
        # On the flipside, this means that for neo-Assyrian purposes, a font is
        # needed that uses the Babylonian glyph for KAM₂ as its glyph for KAM,
        # and the same neo-Assyrian glyph for both KAM₂ and GAN.
        # Then again neo-Assyrian badly needs a new font anyway, all the
        # existing ones are stuck sometime before 2014.
        pass
      elif meszl == '276':
        # Borger writes “Sehr unsicher.” of EZEN×SI?, it is not encoded.
        continue
      elif meszl == '287':
        # See the comments about DUN₃ below.
        pass
      elif row[2].startswith('KASKAL over KASKAL.LAGAB over LAGAB'):
        # It appears that šubtu₄ is not encoded.
        continue
      elif meszl == '303':
        # The neo-Assyrian form is given as KASKAL.UD×EŠ whereas the UR III form
        # is given as KASKAL.UD šeššig, even though UD×EŠ and UD šeššig have the
        # same neo-Assyrian glyph.  Oracc says UD šeššig is correct here, use
        # that.
        pass
      elif meszl == '319':
        # An erroneous entry: The sign name is AL×KID₂ (which is MesZL 475,
        # encoded), the given sign is 𒉒 × 𒋺 NINDA₂×KID₂, which is not present
        # in Borger.
        continue
      elif meszl == '321':
        # NINDA₂×BAN₂, not encoded.
        continue
      elif meszl == '325':
        # NINDA₂×DUB, not encoded, has a question mark in Borger.
        continue
      elif meszl == '328':
        # NINDA₂×ŠID, not encoded, also a question mark.
        continue
      elif meszl == '329':
        # NINDA₂×U₂, not encoded, exists in Borger only with the mention
        # “Aus ÚR×Ú zu erschliessen?”.
        continue
      elif meszl in ('333', '333v3', '333v7'):
        # The ŠAM₂ variants are a mess. Perhaps they are supposed to be partly
        # handled at the font level?
        # TODO(egg): In any case it is incorrect to assign the readings only to
        # the first variant, and then to discard them because it is not encoded;
        # it is easy to find, e.g., NINDA₂×ŠE AN with the reading ša₁₀:
        # https://cdli.ucla.edu/search/archival_view.php?ObjectID=P345814
        continue
      elif meszl in ('334', '335', '337'):
        # More unencoded 𒉒×something signs with no readings.
        continue
      elif meszl == '355':
        # 𒌈 gunû and ×𒃸, not encoded.
        continue
      elif meszl == '364':
        # Borger writes “Wenn es ŠIM×BÚR gegeben hat […]”.  Not encoded.
        continue
      elif meszl == '370':
        continue  # ŠIM×PI, not encoded.
      elif meszl == '379 (sign KAK)':
        # KAK × IGI gunû, is not in Sinacherib, KAK.IGI gunû is used instead.
        continue
      elif ('𒉌𒌓' in row[0] and
            row[0] in row[1] and
            row[0].replace('𒉌𒌓', '𒉌𒂟') in row[1]
            and 'Neo-Assyrian:' in row[1]):
        # Prior to the encoding of NA₄ one had to use either NI.UD or NI.ERIM,
        # the latter being the neo-Assyrian style.  Šašková gives both, with a
        # note.
        pass
      elif row[2].startswith('GA2 x EZEN'):
        # Labat-only variant of 𒃢=GA₂×PA, in parentheses in Labat.
        # Not encoded.
        continue
      elif meszl == '423':
        continue  # Borger writes “unsicher”; not encoded.
      elif meszl == '436':
        # Unencoded neo-Assyrian ligature of NI and GIŠ, with the neo-Assyrian
        # glyph of KISAL.
        continue
      elif meszl in ('456', '456/2'):
        # A sign with uncertain decompositions in Borger, Proto-Ea only.  Not
        # encoded.
        continue
      elif meszl == '460/2':
        continue  # An unencoded variant of 𒁦.
      elif '𒁃' in row[0]:
        # BAḪAR₂ tends to be decomposed (into 𒂁𒋡𒁓) in Assyrian sign lists,
        # but it is its own thing earlier (LAK742) and is encoded separately.
        pass
      elif meszl == '473':
        continue  # GU₄ × KASKAL, not encoded.
      elif meszl == '488/2':
        continue  # Alternative decomposition of 𒎘.
      elif row[2].startswith('SANGA2\n'):
        # In neo-Assyrian 𒊫 looks like 𒅍𒈣𒂀, but Sinacherib does not
        # support it.
        pass
      elif meszl == '520':
        continue  # Lots of question marks in Borger; not encoded.
      elif meszl == '529':
        continue  # LÚ × KU (oder ähnlich); not encoded.
      elif row[2].startswith('ŠU.MIN.MEŠ\n'):
        pass  # Typo in the neo-Assyrian form (ŠU.MIN.AN.MEŠ).
      elif meszl in ('579+?', '579+?+579', '579+579+?'):
        continue  # TODO(egg): I have no idea what is going on with these.
      elif meszl in ('588/2', '588/3'):
        continue  # Unencoded variants.
      elif meszl in ('604', '607'):
        continue  # Unencoded ŠA₃×something signs.
      elif meszl in ('604', '607'):
        continue  # Unencoded ŠA₃×something signs.
      elif meszl in ('624/2', '626'):
        continue  # Some sort of NUNUZ-based mess.
      elif meszl == '636+?':
        continue  # Illegible sign from Labat’s index.
      elif meszl in ('654', '656', '709'):
        continue  # Numeric signs, we handle those separately anyway.
      elif meszl in ('730', '735'):
        pass  # Variants.
      elif meszl in ('741\nalso 882', '882\nalso 741'):
        pass # 𒎔 vs. 𒉾.
      elif meszl == '746+358+?':
        continue  # ???
      elif row[2].startswith('LAGAB x GAR3\n'):
        continue  # That’s a lot of question marks.
      elif meszl == '757':
        pass  # Seems to just be the same sign as ENGUR.
      elif meszl == '796':
        continue  # INDA₂ is not encoded.
      elif meszl == '811':
        continue  # No name, side-by-side ligature of existing signs.
      elif meszl in ('829/2', '829/3'):
        continue  # Unencoded variants.
      elif meszl == '837':
        continue  # Numeric sign.
      elif meszl == '839+086+298+591':
        continue  # Needless decomposition of ASAL₂.
      elif meszl == '845':
        pass  # Typo in the UR III form, A.A×A instead of A×A, handled below.
      elif row[2].startswith('LAK 852\n'):
        pass  # LAK 852, missing in Sinacherib.
      elif meszl == '870':
        # Variants of EN₂. Let’s just pick 𒋙𒀭: looking at Labat, 𒌋𒀭 is the
        # classical Sumerian version, before 𒋙 was a thing; this can be handled
        # at the font level.
        pass
      elif meszl.startswith('XXX'):
        pass  # Ancient signs, not in Borger, not in Sinacherib.
      elif row == ['', '', '', '', '', '']:
        break  # We have reached the end of the table.
      else:
        raise ValueError(row)

    row_index += 1
    readings = ' '.join(row[2].split('\n')[1:-1])
    uncommented_readings = ''
    if not readings:
      readings = '()'
    # Mismatched parentheses; by MesZL number; entries with identical MesZL number
    # are indexed after the slash.
    if meszl in ('69', '598/5', '454'):
      readings = '(' + readings
    elif meszl in (
            '848', '45', '84', '129', '187', '193', '202', '223+889+552',
            '266 (sign LUGAL)', '302+596', '353/2', '469+809+598+590/2',
            '491+380', '491+748', '491+839', '541+184', '545', '724+136',
            '737+755', '839+010+387', '839+756+202', '303'
        ):
      readings += ')'
    elif meszl in ('001+183', '280 (sign EZEN x MIR)', '575+183', '748+183',
                   '493 (sign IL2)\nlater:\n493+201+565'):
      readings = '(' + readings + ')'
    elif meszl in ('242+753', '380+827', '546\nalso 485', '703/2', '883+149', '883+827'):
      if readings[-1] != ')':
        raise ValueError('No trailing parenthesis to strip from readings in %r' % row)
      readings = readings[:-1]
    elif meszl in ('13', '184+464+755'):
      readings = readings.replace('))),', ')),')
    elif meszl in ('701+232+553', '701+232+553/2', '788', '836'):
      readings = readings.replace(')),', '),')
    elif meszl == '84':
      readings = insert_parentheses(readings, '([MesZL: variant of KA x GU (no. 69)];')
    elif meszl == '142':
      readings = insert_parentheses(readings, '(ŠAR5 = IM (no. 641)]')
    elif meszl == '150':
      readings = insert_parentheses(readings, '(Labat; MesZL: ŠURU6 = KID2 (no. 106)]')
    elif meszl == '010+296':
      readings = delete_parentheses(readings, '(= MesZL 296)];')
    elif meszl == '296':
      readings = delete_parentheses(readings, '(= MesZL 296)];')
    elif meszl == '348':
      readings = insert_parentheses(readings, '(MesZL: AL x ŠE (no. 479) = IL (no. 348)];')
    elif meszl == '362+010+120':
      readings = insert_parentheses(readings, ' (nos. 362+010+887+809+807)]')
    elif meszl == '479, 348':
      readings = insert_parentheses(readings, '(no. 348)];')
    elif meszl == '490':
      readings = delete_parentheses(readings, 'PU11, PU8 missing)]')
    elif meszl == '560+132':
      readings = insert_parentheses(readings, '(no. 560)],')
    elif meszl in ('809+816+580', '809+816+584'):
      readings = delete_parentheses(readings, '[MUPARRU')
    elif meszl == '839':
      readings = insert_parentheses(readings, '(no. 856)],')
    elif meszl == '883+381':
      readings = insert_parentheses(readings, '(nos. 382+889)],')
    elif meszl == '092, also 585':
      readings = insert_parentheses(readings, '([MesZL: see MUŠ (no. 585) and PAB (no. 92)];')

    if meszl == '572':
      readings = readings.replace(
          '((MesZL: instead of KAŠŠEBA, KAŠŠEBI)',
          '((MesZL: instead of KAŠŠEBA, KAŠŠEBI);')
    if meszl == '577/2' or meszl == '576/2':
      # We have these glyphs and their readings for proper letter signs;
      # imparting these readings to the punctuation signs (they have separate
      # transcriptions for those roles given in MesZL).
      continue
    if meszl == '863':
      # We have two variants of a numeric sign for IMIN already, the use of a
      # disunified non-numeric sign is unclear, especially since which variant
      # is picked ends up being font-dependent...
      continue

    if readings[0] != '(' or readings[-1] != ')':
      raise ValueError(row)

    processed_readings = ''
    depth = 0
    sign = row[0]
    # Unify BAD squared and IDIM over IDIM squared, see above.
    sign = sign.replace('.𒁁squared', '𒅄')
    sign = sign.replace('𒁁squared', '𒅄')
    sign = sign.replace('𒍗squared', '𒅄')

    if row[2].startswith('TUR3 over TUR3\n'):
      # Borger writes, in Kap. II, entry 147:
      #   Auch TÙR [over] TÙR, genauer [sign] =
      #   NUN [over] NUN gekreuzt (n107) - LAGAR [over] LAGAR.
      # Accordingly, calling this sign TUR3 over TUR3 is imprecise,
      # and certainly it should be unified with
      #   𒉬 NUN CROSSING NUN LAGAR OVER LAGAR,
      # which matches the decomposition given by Borger and has no readings in
      # Šašková.
      sign = '𒉬'

    # Only one variant of TA×ḪI is encoded.
    sign = sign.replace('𒋭\nalso\n𒋫 x 𒄭', '𒋭')
    sign = sign.replace('𒋫 x 𒄭\nalso\n𒋭', '𒋭')

    # See the comment about USAN above.
    sign = sign.replace('𒄛\nand\n𒄘𒉣', '𒄛')

    # See the comments about 244 and 245 above.
    sign = sign.replace('𒁾 x𒊮', '𒌠')
    sign = sign.replace('𒁾 x𒆸', '𒌞')

    # For some reason Šašková does not always use 𒌍, which was there in the
    # initial Unicode 5.0 character set.
    sign = sign.replace('𒌋𒌋𒌋', '𒌍')

    # Use the signs from https://www.unicode.org/wg2/docs/n4277.pdf.
    # Global substitutions: U.U, ME.EŠ, MUNUS.TUG₂, NI.UD, MUNUS.KU, MI.NUNUZ,
    # NI.ERIM, ḪI.GIR₃ are always MAN, MEŠ, NIN, NA₄,NIN₉, GIG, DAG₃, ḪUS
    # respectively.
    sign = sign.replace(
        '𒌋𒌋', '𒎙').replace(
        '𒈨𒌍', '𒎌').replace(
        '𒊩𒌆', '𒎏').replace(
        '𒉌𒌓', '𒎎').replace(
        '𒊩𒆪', '𒎐').replace(
        '𒈪𒉭', '𒍼').replace(
        '𒉌𒂟', '𒍴').replace(
        '𒄭𒄊', '𒍽')

    # Disunification of ŠAR₂ 𒊹 and TI₂ 𒎗.
    if meszl == '633':
      sign = '𒎗'
    # Disunification of ERIM 𒂟 and PIR₂ 𒎕.
    if meszl == '613':
      sign = '𒎕'

    sign = sign.replace('𒅗 x 𒌅', '𒎆')
    sign = sign.replace('𒅗 x 𒌫', '𒎇')
    sign = sign.replace('𒅗 x 𒉺', '𒎄')
    sign = sign.replace('𒅗 x 𒄑', '𒎀')
    sign = sign.replace('𒅗 x 𒄯', '𒎂')
    sign = sign.replace('𒅗 x 𒐋', '𒍿')
    sign = sign.replace('𒅗 x 𒈝', '𒎃')
    sign = sign.replace('𒈹 x 𒍝', '𒎍')
    sign = sign.replace('𒊕 x 𒅊', '𒎖')
    sign = sign.replace('𒀊 x 𒉣', '𒍰')
    sign = sign.replace('𒁾 x 𒊺', '𒍶')
    sign = sign.replace('𒂡 x 𒄞', '𒍷')
    sign = sign.replace('𒂡 x 𒊺', '𒍸')
    sign = sign.replace('𒉒 x 𒁄', '𒎑')
    sign = sign.replace('𒉒 x 𒄀', '𒎒')
    sign = sign.replace('𒂷 x 𒀭𒆕𒀀', '𒍹')
    sign = sign.replace('𒂷 x 𒀾', '𒍺')
    sign = sign.replace('𒁖𒆨 x 𒌑𒈦', '𒍳')
    sign = sign.replace('𒌝 x 𒈨', '𒎘')
    sign = sign.replace('𒈕 x 𒁁', '𒎉')
    sign = sign.replace('𒇽 x 𒋗', '𒎋')
    sign = sign.replace('𒀖 x 𒀀', '𒍱')
    sign = sign.replace('𒀫 x 𒆬', '𒍲')
    sign = sign.replace('𒆸 x 𒄀', '𒎈')

    if sign == '𒀀𒀁':
      sign = '𒀁'  # Typo.

    # TODO(egg): Add the reading ešelal for 𒈀𒇲, and the alternative sign 𒎊.

    # See the extensive discussion of KAM₂ vs. KAMᵛ above.
    sign = sign.replace('𒆚', '𒄰')
    if meszl == '254':
      sign = '𒆚'

    # TODO(egg): investigate 𒌗 vs. 𒌚 for ITI, including in other signs.

    # Unicode has three signs DUN₃ 𒂅, DUN₃ gunû 𒂆, DUN₃ gunû gunû 𒂇; the
    # reference glyphs match the descriptions, they are increasingly gunûd.
    # In neo-Assyrian (or indeed in old Assyrian or old Babylonian) these
    # correspond to two signs, GIN₂ (which has the reading dun₃), and MIR,
    # where MIR=GIN₂ gunû (Borger 556).
    # Šašková assumes that the code point for dun₃(GIN₂) is DUN₃ 𒂅,
    # therefore that MIR = DUN₃ gunû 𒂆, and has no idea what to make of
    # DUN₃ gunû gunû 𒂇.
    # Looking at Labat is enlightening.  The entry 347 for MIR shows two
    # precursor classical sumerian glyphs, one of which is LAK 667 (resembling
    # the reference glyph for 𒂆), and the other one a seemingly unrelated
    # LAK 154; from LAK 667 Labat has an arrow redirecting to entry 595, while
    # LAK 154 morphs into something related to 𒂆 and becomes MIR, one of
    # whose old Babylonian glyphs is the reference glyph for 𒂇.
    # Meanwhile at entry 595 (TUN₃), Labat gives two precursor glyphs
    # resembling the reference glyphs for 𒂅 and 𒂆 (LAK 666 and 667),
    # merging into the latter in Assyrian and Babylonian.
    # It therefore appears that:
    # — LAK 666 is encoded as 𒂅;
    # — LAK 667 is encoded as 𒂆 = LAK 666 gunû;
    # — LAK 154 is encoded as 𒂇 = LAK 667 gunû;
    # — LAK 666 and LAK 667 merge (with the glyph of LAK 667);
    # — the result of this merger is read dun₃ in neo-Assyrian, but it looks
    #   like DUN₃ gunû.
    # We thus get MIR = 𒂇 rather than 𒂆, but the readings of GIN₂ have to
    # be split between DUN₃ 𒂅 and DUN₃ gunû 𒂆 (which will have the same
    # glyph any Assyrian or Babylonian font).
    # The conventions used by Oracc are consistent with the above analysis.
    # The splitting of readings between 𒂅 and 𒂆 is largely a matter of
    # sumerology; we defer to Oracc without further investigation.
    #
    # Šašková consistently uses 𒂆 for MIR, replace that by 𒂇.
    sign = sign.replace('𒂆', '𒂇')
    # Same for a composite sign.
    sign = sign.replace('𒂧', '𒂨')
    # Use 𒂆 wherever Šašková uses 𒂅, we will disunify them below.
    sign = sign.replace('𒂅', '𒂆')

    # Now that we use the correct sign for GIN₂, we have a sign for EZEN×GIN₂.
    sign = sign.replace('𒂡 x 𒂆', '𒂧')

    # Do not decompose 𒁃 nor 𒀷.
    sign = sign.replace('𒂁𒋡𒁓', '𒁃')
    sign = sign.replace('𒀀𒌅𒃮𒇺', '𒀷')
    identical_alternatives = re.match('^([^\0-\ff]*)(,\n|\nor\n)\\1$', sign)
    if ('𒁃' in sign or '𒀷' in sign) and identical_alternatives:
      sign = identical_alternatives.groups()[0]

    if row[2].startswith('GE22\n'):
      sign = '𒍻'

    if meszl == '730':
      sign = sign.split('\nold\n')[0]
    if meszl == '735':
      sign = sign.split('\nnewer\n')[0]

    if row[2].startswith('PEŠ2v\n'):
      sign = '𒎔'
    if row[2].startswith('PEŠ2\n'):
      sign = '𒉾'

    if meszl == '757':
      sign = '𒇉'  # ZIKUM = ENGUR.

    if meszl == '870':
      sign = '𒋙𒀭'

    if not sign or any(is_printable_basic_latin(c) for c in sign):
      raise ValueError('sign = "%s", in row %s' % (sign, row))

    first_reading = Reading(sign, row_index)
    first_reading.value = row[2].split('\n')[0]

    if sign == '𒇽𒇽' and first_reading.value == 'LU2 over LU2':
      # Not encoded, same reading as LU2.LU2 which is in the list.
      continue

    sign_readings = [first_reading]
    current_reading = first_reading
    for c in readings:
      processed_readings += c
      if depth == 1 and c in ',;':
        current_reading = Reading(sign, row_index)
        sign_readings.append(current_reading)
        continue  # Consume delimiters between comments.
      if c == '(':
        depth += 1
        if depth in (1, 2):
          continue  # Consume the initial & start-of-comment parentheses.
      elif c == ')':
        depth -= 1
        if depth in (0, 1):
          continue  # Consume the final & end-of-comment parentheses.

      if depth == 1:
        if current_reading is first_reading:
          current_reading = Reading(sign, row_index)
          sign_readings.append(current_reading)
        current_reading.value += c
        if current_reading.comment:
          raise ValueError(
              'Reading %s restarts after comment %s [MesZL %s]' % (
                  current_reading.value, current_reading.comment, meszl))
      elif depth > 1:
        current_reading.comment += c
      else:
        raise ValueError('surfaced before end of readings: %s[!] %r' % (processed_readings, row))
    if depth != 0:
      raise ValueError('depth=%d at end of readings %r' % (depth, row))
    for reading in sign_readings:
      reading.normalize()
    # We handle numbers ourselves, and thus discard any numerical readings
    # found in Šašková.
    sign_readings = [
        reading for reading in sign_readings
        if any (c.isalpha() for c in reading.value)]

    # Deal with the disunification of 60 and 1 in Unicode.
    for reading in sign_readings:
      # Readings given for 60 in MesZL 748.
      if reading.sign == '𒁹' and reading.value in ('GEŠ2', 'GIŠ2', 'GEŠTA'):
        reading.sign = '𒐕'
      # Labat-only readings for 60n.
      if reading.sign == '𒐊' and reading.value == 'GEŠIA':
        reading.sign = '𒐙'
      if reading.sign == '𒐋' and reading.value == 'GEŠAŠ':
        reading.sign = '𒐚'
      if reading.sign in '𒐌𒑂' and reading.value == 'GEŠUMUN':
        reading.sign = '𒐛'
      if reading.sign in '𒐍𒑄' and reading.value == 'GEŠUSSU':
        reading.sign = '𒐜'
      if reading.sign == '𒑆' and reading.value == 'GEŠILIMMU':
        reading.sign = '𒐝'

      if '𒂆' in reading.sign and all(is_composition_character(c.lower())
                                       for c in reading.value):
        try:
          reading.sign = reading.sign.replace('𒂆',
                                              DUN3_VARIANTS[reading.value])
        except KeyError as e:
          print(', '.join(unicodedata.name(c).replace('CUNEIFORM SIGN ', '')
                          for c in reading.sign),
                file=sys.stderr)
          raise

    for reading in sign_readings:
      readings_by_value.setdefault(reading.value, []).append(reading)
      readings_by_sign.setdefault(reading.sign, []).append(reading)
    ok_entries += 1

# Insert the numbers which we listed ourselves.
for sign, compositions in numbers.compositions_by_sign.items():
  for composition in compositions:
    reading = Reading(sign, šašková_index=None)
    reading.value = composition
    readings_by_value.setdefault(reading.composition, []).append(reading)
    readings_by_sign.setdefault(reading.sign, []).append(reading)

# Punctuation and common determinatives.
for sign, compositions in {
    # MesZL 592.
    '𒑱' : [':'],
    # MesZL 576: Trennungszeichen (wie n592; Umschrift :).  Disunified from GAM
    # in Unicode.
    '𒑲' : [':v1'],
    # MesZL 577: Trennungs- und Wiederholungszeichen (Umschrift mit Parpola,
    # LASEA pXX ⫶).  Disunified from ILIMMU4 in Unicode.
    '𒑳' : ['⫶'],
    # Word divider.  See MesZL 748, p. 418: In Kültepe wird ein senkrechter Keil
    # als Worttrenner gebraucht.  Disunified from DIŠ in Unicode.
    # See AAA 1/3, 01 for an example usage:
    # https://cdli.ucla.edu/search/archival_view.php?ObjectID=P360975.
    # We use the transcription convention from CDLI, a forward slash.
    '𒑰' : ['/'],
    # Determinatives for personal names and gods.
    '𒁹' : ['m'],
    '𒊩' : ['f'],
    '𒀭' : ['d'],
  }.items():
  for composition in compositions:
    reading = Reading(sign, šašková_index=None)
    reading.value = composition
    readings_by_value.setdefault(reading.composition, []).append(reading)
    readings_by_sign.setdefault(reading.sign, []).append(reading)

readings_by_composition = {}

def recompute_readings_by_composition():
  readings_by_composition.clear()
  for readings in readings_by_sign.values():
    for reading in readings:
      readings_by_composition.setdefault(reading.composition(), []).append(reading)

def sign_name(sign):
  return readings_by_sign[sign][0].value

def print_readings(value, readings, by_source=False):
  print(value, file=sys.stderr)
  for reading in readings:
    print('    ', reading.source.ljust(6) if by_source else ('...' + reading.disambiguator.ljust(8)),
          reading.sign, sign_name(reading.sign), 8 * ' ', reading.comment, file=sys.stderr)

for value, readings in readings_by_value.items():
  if len(readings) > 1:
    # Duplicates, with inconsistent duplicates explicitly listed.
    for reading in readings:
      if not reading.keep:
        continue
      for other in readings:
        if other.keep and other.sign == reading.sign and other is not reading:
          if (other.keep and
              ((other.comment and reading.comment and other.comment != reading.comment) or
               (other.source and reading.source and other.source != reading.source)) and
              (value, sign_name(reading.sign)) not in (
                  # One entry is a superset of the other.
                  ('IL', 'AL x ŠE'),
                  # The comments on these Labat readings are inconsistent
                  # (MesZL: AŠLAG missing vs. MesZL: AŠLAG = TUG2.UD), the
                  # latter being right.
                  ('AŠLAG', 'GIŠ.TUG2.PI.KAR'),
                  # MesZL and Labat readings in agreement, with a ? from MesZL.
                  ('GAMBI', 'MUNUS.UŠ.DI'),
                  # MesZL 905 and 906 unified in Unicode (as in Labat).
                  ('MUR7', 'SIG4'),
                  # Duplicate entries for variants of TA×ḪI unified by Unicode
                  # as 𒋭.  They differ only by their comment.
                  ('ALAMMUŠ', 'LAL3'),
                  ('ALAMUŠ', 'LAL3'),
              )):
            print_readings(value, readings, by_source=True)
            raise ValueError('Inconsistent duplicate readings')
          other.keep = False
    # Ambiguous readings coming from inconsistency between sign lists.
    if any(reading.source and reading.source != 'MesZL' for reading in readings):
      for reading in readings:
        if not reading.source:
          implicit_meszl = any(
              re.match(
                  other.comment,
                  'MesZL: (\w+, *)*%s(, *\w+)* = %s' % (value, readings_by_sign[reading.sign][0].value))
              for other in readings)
          if implicit_meszl:
            reading.source = 'MesZL'
          else:
            print_readings(value, readings, by_source=True)
            raise ValueError("Divergent readings with undetermined source")
      if not all(reading.source == readings[0].source for reading in readings):
        for reading in readings:
          reading.disambiguator += reading.source[0]

for reading_dict in (readings_by_sign,
                     readings_by_value):
  filtered_dict = {
      key: [reading for reading in readings if reading.keep]
      for key, readings in reading_dict.items()
  }
  reading_dict.clear()
  reading_dict.update(filtered_dict)

recompute_readings_by_composition()

for readings in readings_by_composition.values():
  if len(readings) > 1:
    readings.sort(key=lambda r: r.šašková_index)
    i = 0
    for reading in readings:
      if i:
        reading.disambiguator += 'v%d' % i
      i += 1

recompute_readings_by_composition()

for composition, readings in readings_by_composition.items():
  if len(readings) > 1:
    print_readings(composition, readings)
    raise ValueError('Ambiguous composition')

# Sanity check of numbers: 1meow and meow must map to the same sign.
for composition, readings in readings_by_composition.items():
  if re.match('^1\D', composition):
    if composition[1:] in readings_by_composition:
      if readings[0].sign != readings_by_composition[composition[1:]][0].sign:
        if composition in ('1iku', '1buru'):
          # Borger gives iku as a reading for 𒃷 in 𒀸𒃷.  Friberg sees that as
          # a determinative, and transcribes it 1iku GAN2.  Shrug.
          # Buru seems wtf.
          continue
        print_readings(composition, readings)
        print_readings(composition[1:], readings_by_composition[composition[1:]])
        raise ValueError('Inconsistent numeric readings')

for composition, readings in readings_by_composition.items():
  if (not all(is_composition_character(c.lower()) for c in composition) or
      composition.startswith('x')):
    # TODO(egg): composition.startswith('x') is a cheesy way to eliminate xv,
    # which happens to be the only reading wherein x is not ₓ at this point.
    continue
  print('"%s"="%s"' % (composition, readings[0].sign))
