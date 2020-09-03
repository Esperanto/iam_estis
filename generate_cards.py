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

CardType = collections.namedtuple('CardType', ['name', 'color'])

CARD_TYPE_MAP = {
    'Event': CardType('Evento', 'FF4040'),
    'Thing': CardType('Aĵo', '4040FF'),
    'Aspect': CardType('Trajto', '40FF40'),
    'Character': CardType('Rolulo', 'FFFF40'),
    'Place': CardType('Loko', '40FFFF'),
    'Ending': CardType('Fino', 'FF40FF'),
}

POINTS_PER_MM = 2.8346457

PAGE_WIDTH = 210
PAGE_HEIGHT = 297

CARDS_START = (124.0 * 210.0 / 2480.0, 194.0 * 210.0 / 2480.0)
CARD_SIZE = (744.0 * 210.0 / 2480.0, 1039.0 * 210.0 / 2480.0)

PAGE_BORDER_SIZE = 24 * 210.0 / 2480.0

CROSS_SIZE = 31 * 210.0 / 2480.0
INSET = 5

#1012 1188
PARAGRAPH_START = (1012 - 194) * 210 / 2480.0
PARAGRAPH_HEIGHT = 14.903

current_page = 1

def render_paragraph(cr, text, font = "Serif 9"):
    cr.save()

    cr.set_source_rgb(100 / 255.0, 0, 0)

    # Remove the mm scale
    cr.scale(1.0 / POINTS_PER_MM, 1.0 / POINTS_PER_MM)

    layout = PangoCairo.create_layout(cr)
    m = re.match(r'(.*?)([0-9]+(\.[0-9]*)?)$', font)
    font_size = float(m.group(2))
    font = m.group(1) + str(font_size)
    fd = Pango.FontDescription.from_string(font)
    layout.set_font_description(fd)
    layout.set_width((CARD_SIZE[0] - INSET * 2) * POINTS_PER_MM
                     * Pango.SCALE)
    layout.set_text(text, -1)
    layout.set_alignment(Pango.Alignment.CENTER)

    (ink_rect, logical_rect) = layout.get_pixel_extents()

    cr.move_to(INSET * POINTS_PER_MM,
               (PARAGRAPH_START + PARAGRAPH_HEIGHT / 2) *
               POINTS_PER_MM -
               logical_rect.height / 2.0)

    PangoCairo.show_layout(cr, layout)

    cr.restore()

    return logical_rect.height / POINTS_PER_MM

def card_border(cr):
    cr.save()
    cr.rectangle(-PAGE_BORDER_SIZE,
                 -PAGE_BORDER_SIZE,
                 CARD_SIZE[0] + PAGE_BORDER_SIZE * 2,
                 CARD_SIZE[1] + PAGE_BORDER_SIZE * 2)
    cr.fill()
    cr.restore()

def generate_card(cr, card_type, text):
    color = [int(card_type.color[x : x + 2], 16) / 255
             for x in range(0, len(card_type.color), 2)]
    cr.set_source_rgb(*color)
    card_border(cr)

    render_paragraph(cr, text, "Kaushan Script 9")

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
