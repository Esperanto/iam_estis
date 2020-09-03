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

POINTS_PER_MM = 2.8346457

PAGE_WIDTH = 210
PAGE_HEIGHT = 297

CARDS_START = (124.0 * 210.0 / 2480.0, 194.0 * 210.0 / 2480.0)
CARD_SIZE = (744.0 * 210.0 / 2480.0, 1039.0 * 210.0 / 2480.0)

PAGE_BORDER_SIZE = 24 * 210.0 / 2480.0

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
    cr.set_source_rgb(100 / 255.0, 0.9, 0.9)
    cr.fill()
    cr.restore()

def generate_card(cr, text):
    card_border(cr)

    render_paragraph(cr, text, "Kaushan Script 9")

def end_page(cr):
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

        generate_card(cr, text)

        cr.restore()

        card_num += 1

        if card_num >= 9:
            end_page(cr)
            card_num = 0

end_page(cr)
