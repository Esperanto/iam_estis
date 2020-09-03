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
    return Rsvg.Handle.new_from_file(fn)

CardType = collections.namedtuple('CardType', ['name', 'color', 'icon'])

ENDING_TYPE = CardType('Fino', 'FF40FF', None)

CARD_TYPE_MAP = {
    'Event': CardType('Evento', 'FF4040', None),
    'Thing': CardType('Aĵo', '4040FF', None),
    'Aspect': CardType('Trajto', '40FF40', None),
    'Character': CardType('Rolulo', 'FFFF40', None),
    'Place': CardType('Loko', '40FFFF', load_svg('loko.svg')),
    'Ending': ENDING_TYPE,
}

POINTS_PER_MM = 2.8346457

PAGE_WIDTH = 210
PAGE_HEIGHT = 297

CARDS_START = (124.0 * 210.0 / 2480.0, 194.0 * 210.0 / 2480.0)
CARD_SIZE = (744.0 * 210.0 / 2480.0, 1039.0 * 210.0 / 2480.0)

CARD_BORDER_SIZE = 12 * 210 / 2480.0

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

def render_paragraph(cr, text, font):
    layout = get_paragraph_layout(text, font)
    layout.set_width((CARD_SIZE[0] - INSET * 2) * POINTS_PER_MM
                     * Pango.SCALE)
    layout.set_alignment(Pango.Alignment.CENTER)
    (ink_rect, logical_rect) = layout.get_pixel_extents()

    cr.save()

    # Remove the mm scale
    cr.scale(1.0 / POINTS_PER_MM, 1.0 / POINTS_PER_MM)

    cr.move_to(INSET * POINTS_PER_MM,
               PARAGRAPH_END * POINTS_PER_MM -
               logical_rect.height)

    PangoCairo.show_layout(cr, layout)

    cr.restore()

    return logical_rect.height / POINTS_PER_MM

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
               (CARD_BORDER_SIZE + TITLE_SIZE / 2) * POINTS_PER_MM -
               logical_rect.height / 2)
    PangoCairo.show_layout(cr, layout)
    cr.restore()

def card_icon(cr, icon):
    dim = icon.get_dimensions()

    scale = (TITLE_SIZE - CARD_BORDER_SIZE * 2) / dim.height
    cr.save()
    cr.translate(CARD_BORDER_SIZE, CARD_BORDER_SIZE)
    cr.scale(scale, scale)
    icon.render_cairo(cr)
    cr.restore()

def generate_card(cr, card_type, text):
    color = [int(card_type.color[x : x + 2], 16) / 255
             for x in range(0, len(card_type.color), 2)]
    cr.set_source_rgb(*color)
    card_border(cr)
    card_title(cr, card_type.name)

    if card_type.icon:
        card_icon(cr, card_type.icon)

    if card_type == ENDING_TYPE:
        font_size = 15
    else:
        font_size = 9

    render_paragraph(cr, text, "Kaushan Script {}".format(font_size))

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
with open("iam_estis.csv", "rt", encoding="utf-8") as f:
    for line_num, line in enumerate(f):
        if line_num < 3:
            continue

        parts = line.rstrip().split("\t")

        if len(parts) < 6:
            continue

        text = parts[5].strip()

        if len(text) <= 0:
            continue

        cr.save()

        cr.translate(card_num % 3 * CARD_SIZE[0] + CARDS_START[0],
                     card_num // 3 * CARD_SIZE[1] + CARDS_START[1])

        generate_card(cr, CARD_TYPE_MAP[parts[3]], text)

        cr.restore()

        card_num += 1

        if card_num >= 9:
            end_page(cr)
            card_num = 0

end_page(cr)
