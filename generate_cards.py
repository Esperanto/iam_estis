#!/usr/bin/env python3

import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg
gi.require_version('Pango', '1.0')
from gi.repository import Pango
gi.require_version('PangoCairo', '1.0')
from gi.repository import PangoCairo
import cairo
import math
import re
import collections

def load_svg(fn):
    return Rsvg.Handle.new_from_file('images/{}'.format(fn))

CardType = collections.namedtuple('CardType', ['name', 'color', 'icon'])

ENDING_TYPE = CardType('Fino', '252422', load_svg('fino.svg'))

CARD_TYPE_MAP = {
    'Event': CardType('Evento', '9A031E', load_svg('evento.svg')),
    'Thing': CardType('Aĵo', '0F4C5C', load_svg('aĵo.svg')),
    'Aspect': CardType('Trajto', 'E36414', load_svg('trajto.svg')),
    'Character': CardType('Rolulo', '5F0F40', load_svg('rolulo.svg')),
    'Place': CardType('Loko', 'FB8B24', load_svg('loko.svg')),
    'Ending': ENDING_TYPE,
}

class Card:
    class BadRow(Exception):
        pass

    class BadData(Exception):
        pass

    def __init__(self, row):
        parts = row.rstrip().split("\t")

        if len(parts) < 6:
            raise Card.BadRow

        self.text = parts[5].strip()

        if len(self.text) <= 0:
            raise Card.BadCard

        self.image = None

        try:
            image_fn = parts[6]
        except IndexError:
            pass
        else:
            self.image = load_svg(image_fn)

        self.type = CARD_TYPE_MAP[parts[3]]

        interrupt = parts[4].strip()

        if interrupt == "":
            self.interrupt = False
        elif interrupt == "Y":
            self.interrupt = True
        else:
            raise Card.BadData("Invalid value for Interrupt “{}”".
                               format(interrupt))

POINTS_PER_MM = 2.8346457

PAGE_WIDTH = 210
PAGE_HEIGHT = 297

CARDS_START = (124.0 * 210.0 / 2480.0, 194.0 * 210.0 / 2480.0)
CARD_SIZE = (744.0 * 210.0 / 2480.0, 1039.0 * 210.0 / 2480.0)

CARD_BORDER_SIZE = 3

TITLE_SIZE = 12

CROSS_SIZE = 31 * 210.0 / 2480.0
INSET = 5

#1012 1188
PARAGRAPH_START = (1012 - 194) * 210 / 2480.0
PARAGRAPH_HEIGHT = 14.903
PARAGRAPH_END = PARAGRAPH_START + PARAGRAPH_HEIGHT

current_page = 1

def get_paragraph_layout(text, font):
    layout = PangoCairo.create_layout(cr)
    m = re.match(r'(.*?)([0-9]+(\.[0-9]*)?)$', font)
    font_size = float(m.group(2))
    font = m.group(1) + str(font_size)
    fd = Pango.FontDescription.from_string(font)
    layout.set_font_description(fd)
    layout.set_text(text, -1)

    return layout

def render_ending(cr, text):
    layout = get_paragraph_layout(text, "Kaushan Script 15")
    layout.set_width((CARD_SIZE[0] - INSET * 2) * POINTS_PER_MM
                     * Pango.SCALE)
    layout.set_alignment(Pango.Alignment.CENTER)
    (ink_rect, logical_rect) = layout.get_pixel_extents()

    cr.save()

    # Remove the mm scale
    cr.scale(1.0 / POINTS_PER_MM, 1.0 / POINTS_PER_MM)

    top_offset = TITLE_SIZE + CARD_BORDER_SIZE * 2
    text_height = CARD_SIZE[1] - top_offset - CARD_BORDER_SIZE

    cr.move_to(INSET * POINTS_PER_MM,
               (top_offset + text_height / 2) * POINTS_PER_MM -
               logical_rect.height / 2)

    PangoCairo.show_layout(cr, layout)

    cr.restore()

def render_name(cr, text):
    layout = get_paragraph_layout(text, "Kaushan Script 11")
    (ink_rect, logical_rect) = layout.get_pixel_extents()

    cr.save()

    # Remove the mm scale
    cr.scale(1.0 / POINTS_PER_MM, 1.0 / POINTS_PER_MM)

    cr.move_to(CARD_SIZE[0] / 2 * POINTS_PER_MM -
               logical_rect.width / 2,
               PARAGRAPH_END * POINTS_PER_MM -
               logical_rect.height)

    PangoCairo.show_layout(cr, layout)

    cr.restore()

def card_border(cr):
    cr.save()
    cr.rectangle(0, 0, *CARD_SIZE)
    cr.rectangle(CARD_SIZE[0] - CARD_BORDER_SIZE,
                 CARD_BORDER_SIZE + TITLE_SIZE,
                 CARD_BORDER_SIZE * 2 - CARD_SIZE[0],
                 CARD_SIZE[1] - CARD_BORDER_SIZE * 2 - TITLE_SIZE)
    cr.fill()
    cr.restore()

def card_title(cr, title):
    layout = get_paragraph_layout(title, "Kaushan Script 9")
    (ink_rect, logical_rect) = layout.get_pixel_extents()

    cr.save()
    # Remove the mm scale
    cr.scale(1.0 / POINTS_PER_MM, 1.0 / POINTS_PER_MM)
    cr.set_source_rgb(1, 1, 1)
    cr.move_to((CARD_SIZE[0] - CARD_BORDER_SIZE) * POINTS_PER_MM -
               logical_rect.width,
               (CARD_BORDER_SIZE + TITLE_SIZE) / 2 * POINTS_PER_MM -
               logical_rect.height / 2)
    PangoCairo.show_layout(cr, layout)
    cr.restore()

def card_image(cr, image):
    dim = image.get_dimensions()

    scale = (CARD_SIZE[0] - CARD_BORDER_SIZE * 4) / max(dim.width, dim.height)
    cr.save()
    cr.translate(CARD_SIZE[0] / 2 - dim.width * scale / 2,
                 CARD_SIZE[1] / 2 - dim.height * scale / 2)
    cr.scale(scale, scale)
    image.render_cairo(cr)
    cr.restore()

def card_icon(cr, icon):
    dim = icon.get_dimensions()

    scale = (TITLE_SIZE - CARD_BORDER_SIZE) / dim.height
    cr.save()
    cr.translate(CARD_BORDER_SIZE, CARD_BORDER_SIZE)
    cr.scale(scale, scale)
    icon.render_cairo(cr)
    cr.restore()

def render_interrupt(cr, card_type):
    with open('images/interrompo.svg', 'rt', encoding='utf-8') as f:
        icon_data = f.read().replace('#ff0000', '#{}'.format(card_type.color))

    icon = Rsvg.Handle.new_from_data(icon_data.encode('utf-8'))
    dim = icon.get_dimensions()

    scale = (CARD_SIZE[0] - CARD_BORDER_SIZE * 2) / dim.width

    cr.save()
    cr.translate(CARD_BORDER_SIZE,
                 CARD_SIZE[1] / 2 - dim.height / 2 * scale)
    cr.scale(scale, scale)
    icon.render_cairo(cr)
    cr.restore()

def generate_card(cr, card):
    color = [int(card.type.color[x : x + 2], 16) / 255
             for x in range(0, len(card.type.color), 2)]
    cr.set_source_rgb(*color)
    card_border(cr)
    card_title(cr, card.type.name)

    if card.interrupt:
        render_interrupt(cr, card.type)

    if card.image:
        card_image(cr, card.image)

    if card.type.icon:
        card_icon(cr, card.type.icon)

    if card.type == ENDING_TYPE:
        render_ending(cr, card.text)
    else:
        render_name(cr, card.text)

def draw_cross(cr):
    cr.save()
    cr.set_line_width(0.2)

    cr.move_to(-CROSS_SIZE, 0)
    cr.rel_line_to(CROSS_SIZE * 2, 0)
    cr.move_to(0, -CROSS_SIZE),
    cr.rel_line_to(0, CROSS_SIZE * 2)

    cr.arc(CROSS_SIZE, CROSS_SIZE, CROSS_SIZE, math.pi, 3 * math.pi / 2)

    cr.arc(CROSS_SIZE, -CROSS_SIZE,
           CROSS_SIZE,
           math.pi / 2, math.pi)

    cr.arc(-CROSS_SIZE, -CROSS_SIZE,
           CROSS_SIZE,
           0, math.pi / 2)

    cr.arc(-CROSS_SIZE, CROSS_SIZE,
           CROSS_SIZE,
           3 * math.pi / 2, math.pi * 2)

    cr.stroke()
    cr.restore()

def end_page(cr):
    for y in range(3):
        for x in range(3):
            for off_x in [0, CARD_SIZE[0]]:
                if x != 2 and off_x > 0:
                    continue
                for off_y in [0, CARD_SIZE[1]]:
                    if y != 2 and off_y > 0:
                        continue
                    cr.save()
                    cr.translate(CARDS_START[0] + x * CARD_SIZE[0] + off_x,
                                 CARDS_START[1] + y * CARD_SIZE[1] + off_y)
                    draw_cross(cr)
                    cr.restore()

    cr.show_page()

# Make a PDF version of the cards

surface = cairo.PDFSurface("iam_estis.pdf",
                           PAGE_WIDTH * POINTS_PER_MM,
                           PAGE_HEIGHT * POINTS_PER_MM)

cr = cairo.Context(surface)

# Use mm for the units from now on
cr.scale(POINTS_PER_MM, POINTS_PER_MM)

# Use ½mm line width
cr.set_line_width(0.5)

card_num = 0
with open("iam_estis.tsv", "rt", encoding="utf-8") as f:
    for line_num, line in enumerate(f):
        if line_num < 1:
            continue

        try:
            card = Card(line)
        except Card.BadRow:
            continue

        cr.save()

        cr.translate(card_num % 3 * CARD_SIZE[0] + CARDS_START[0],
                     card_num // 3 * CARD_SIZE[1] + CARDS_START[1])

        generate_card(cr, card)

        cr.restore()

        card_num += 1

        if card_num >= 9:
            end_page(cr)
            card_num = 0

end_page(cr)
