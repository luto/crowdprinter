import logging
import re
import traceback
from typing import Literal

import cadquery as cq


class SignContent:
    text: str
    braille: str

    def __init__(self, text: str, braille: str):
        self.text = text.strip()
        braille = braille.strip().replace(" ", "\u2800")
        if re.fullmatch(r"[⠀-⠿\n]+", braille) is None and len(braille) > 0:
            raise ValueError(
                "Braille can only contain chars from the Unicode braille block, spaces and new-lines"
            )
        self.braille = braille


class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __len__(self):
        return 2

    def __getitem__(self, index):
        return (self.x, self.y)[index]

    def __str__(self):
        return "({}, {})".format(self.x, self.y)


class Braille:
    horizontal_interdot = 2.5
    vertical_interdot = 2.5
    intercell = 6.4
    interline = 11
    dot_height = 1.2
    dot_diameter = 1

    def brailleToPoints(self, text):
        # Unicode bit pattern (cf. https://en.wikipedia.org/wiki/Braille_Patterns).
        mask1 = 0b00000001
        mask2 = 0b00000010
        mask3 = 0b00000100
        mask4 = 0b00001000
        mask5 = 0b00010000
        mask6 = 0b00100000
        mask7 = 0b01000000
        mask8 = 0b10000000
        masks = (mask1, mask2, mask3, mask4, mask5, mask6, mask7, mask8)

        # Corresponding dot position
        w = self.horizontal_interdot
        h = self.vertical_interdot
        pos1 = Point(0, 2 * h)
        pos2 = Point(0, h)
        pos3 = Point(0, 0)
        pos4 = Point(w, 2 * h)
        pos5 = Point(w, h)
        pos6 = Point(w, 0)
        pos7 = Point(0, -h)
        pos8 = Point(w, -h)
        pos = (pos1, pos2, pos3, pos4, pos5, pos6, pos7, pos8)

        # Braille blank pattern (u'\u2800').
        blank = "⠀"
        points = []
        # Position of dot1 along the x-axis (horizontal).
        character_origin = 0
        for c in text:
            for m, p in zip(masks, pos):
                delta_to_blank = ord(c) - ord(blank)
                if m & delta_to_blank:
                    points.append(p + Point(character_origin, 0))
            character_origin += self.intercell
        return points


class Sign:
    def __init__(
        self,
        content: SignContent,
        min_width: float = 10,
        max_width: float = 210,
        min_height: float = 30,
        max_height: float = 210,
        thickness: float = 2,
        corner_radius: float = 5,
        border_thickness: float = 1,
        border_distance: float = 2,
        font_size: float = 14,
        font_thickness: float = 1.5,
        font: str = "",
        font_style: Literal["regular", "bold", "italic"] = "bold",
        font_chamfer: float = 2,
        padding: float = 5,
        content_box_padding: float = 5 * 2,
        has_qr_code: bool = False,
        qr_code_width: float = 50,
        qr_code_height: float = 50,
        qr_code_edge_len: float = 20,
        text_start_mark_size: float = 8,
        braille_start_mark_size: float = 8,
        start_mark: bool = False,
        fast: bool = False,
    ):
        self.content = content
        self.min_width = min_width
        self.max_width = max_width
        self.min_height = min_height
        self.max_height = max_height
        self.thickness = thickness
        self.corner_radius = corner_radius
        self.border_thickness = border_thickness
        self.border_distance = border_distance
        self.font_size = font_size
        self.font_thickness = font_thickness
        self.font = font
        self.font_style = font_style
        self.font_chamfer = font_chamfer
        self.padding = padding
        self.content_box_padding = content_box_padding
        self.has_qr_code = has_qr_code
        self.qr_code_width = qr_code_width
        self.qr_code_height = qr_code_height
        self.qr_code_edge_len = qr_code_edge_len
        self.text_start_mark_size = text_start_mark_size
        self.braille_start_mark_size = braille_start_mark_size
        self.start_mark = start_mark
        self.fast = fast

    def generate_background(self, width, height, thickness):
        return (
            cq.Workplane()
            .box(width, height, thickness)
            .edges("|Z")
            .fillet(self.corner_radius)
            .translate((width / 2, -height / 2, 0))
        )

    def generate_border(self, width, height, thickness):
        return (
            cq.Workplane()
            .box(
                width - self.border_distance * 2,
                height - self.border_distance * 2,
                self.border_thickness,
            )
            .edges("|Z")
            .fillet(self.corner_radius - self.border_distance)
            .faces("+Z or -Z")
            .shell(self.border_thickness)
            .translate((width / 2, -height / 2, 0))
        )

    def generate_qr(self, width, height, thickness):
        r = (
            cq.Workplane()
            .rect(width + self.border_thickness, height + self.border_thickness)
            .rect(width, height)
            .extrude(self.thickness)
        )
        r = r.rect(
            width + self.border_thickness, height - self.qr_code_edge_len
        ).cutThruAll()
        r = r.rect(
            width - self.qr_code_edge_len, height + self.border_thickness
        ).cutThruAll()
        r = r.translate(
            (
                (width + self.border_thickness) / 2,
                -(height + self.border_thickness) / 2,
                0,
            )
        )
        return r

    def generate_start_mark(self, size, shape=3):
        r = (
            cq.Workplane()
            .polygon(3, size)
            .extrude(self.thickness + self.border_thickness)
            .translate((0, 0, -self.thickness / 2))
        )
        return r

    def _chamfer(self, w, r):
        i = r.wires().vals().index(w)
        r = (
            r.wires()
            .item(i)
            .toPending()
            .offset2D(1, "arc")
            .extrude(self.font_thickness)
        )
        return r
        # try:
        #    i = r.wires().vals().index(w)
        #    r = r.wires().item(i).chamfer(self.font_chamfer)
        # except OCP.StdFail.StdFail_NotDone:
        #    print(traceback.format_exc())
        # finally:
        #    return r

    def _mk_chamfer(self, pnt):
        print("mewo")
        return cq.Solid.makeCone(1, 0.1, 1).locate(pnt)

    def generate_text(
        self,
        string: str,
        size: float,
        height: float,
        chamfer: float,
        rounded_chamfer=True,
    ):
        faces = (
            cq.Workplane()
            .text(
                string,
                size,
                height,
                fontPath=self.font,
                kind=self.font_style,
                valign="top",
                halign="left",
            )
            .faces(">Z")
            .vals()
        )
        out = cq.Workplane("XY")
        for face in faces:
            try:
                wires = cq.Workplane("XY").add(face).toPending().wires().vals()
                tmp_wp = cq.Workplane("XY")
                is_first = 1
                for wire in wires:
                    outline = (
                        cq.Workplane("XY")
                        .add(wire)
                        .toPending()
                        .offset2D(is_first * chamfer, "arc")
                    )
                    if rounded_chamfer:
                        outline = outline.offset2D(-is_first * 0.001, "arc")
                        finished_chamfer = chamfer - 0.005
                    else:
                        finished_chamfer = chamfer - 0.2
                    tmp_wp.add(outline)
                    is_first = -1
                if self.fast:
                    out.add(tmp_wp.wires().toPending().extrude(-height - 0.1))
                else:
                    out.add(
                        tmp_wp.wires()
                        .toPending()
                        .extrude(-height - 0.1)
                        .edges(">Z")
                        .chamfer(finished_chamfer)
                    )
            except:  # NOQA
                logging.warn(traceback.format_exc())
        return out

    def generate_braille(self, string: str):
        dot_pos = []
        line_start_pos = Point(0, -Braille.intercell)
        for text in string.split("\n"):
            dots = Braille().brailleToPoints(text)
            dots = [p + line_start_pos for p in dots]
            dot_pos += dots
            line_start_pos += Point(0, -Braille.interline)

        d = Braille.dot_diameter
        if self.fast:
            r = (
                cq.Workplane()
                .pushPoints(dot_pos)
                .circle(d)
                .extrude(Braille.dot_height)
                .translate((d * 2, 0, 0))
            )
        else:
            r = (
                cq.Workplane()
                .pushPoints(dot_pos)
                .circle(d)
                .extrude(Braille.dot_height)
                .faces(">Z")
                .edges()
                .fillet(d - 0.001)
                .translate((d * 2, 0, 0))
            )
        return r

    def render(self):
        if (
            len(self.content.text) == 0
            and len(self.content.braille) == 0
            and not self.has_qr_code
        ):
            raise ValueError("Can't create empty sign")
        content = cq.Workplane()
        text_pos = (0, 0, 0)
        braille_pos = (0, 0, 0)
        if len(self.content.text) > 0:
            text = self.generate_text(
                self.content.text,
                self.font_size,
                self.font_thickness,
                self.font_chamfer,
            )
            text_box = text.combine().objects[0].BoundingBox()
            text_pos = (-text_box.xmin, -text_box.ymax, 0)
            braille_pos = (0, -(text_box.ylen + self.content_box_padding), 0)
            content = content.add(text.translate(text_pos))

        if len(self.content.braille) > 0:
            braille = self.generate_braille(self.content.braille)
            braille_box = braille.combine().objects[0].BoundingBox()
            content = content.add(
                braille.translate(braille_pos).translate(
                    (-braille_box.xmin, -braille_box.ymax, 0)
                )
            )

        try:
            content_box = content.combine().objects[0].BoundingBox()
            content_width = content_box.xlen
            content_height = content_box.ylen
        except IndexError:
            content_width = 0
            content_height = 0

        if self.has_qr_code:
            qr = self.generate_qr(
                self.qr_code_width, self.qr_code_height, self.border_thickness
            )
            qr_box = qr.combine().objects[0].BoundingBox()
            if content_width > 0 and content_height > 0:
                qr_intersect = (
                    cq.Workplane()
                    .box(content_width, qr_box.ylen, self.thickness)
                    .translate((content_width / 2, -qr_box.ylen / 2, 0))
                )
                intersection = content.intersect(
                    qr_intersect.translate((0, -(content_height - qr_box.ylen), 0))
                )
                intersection_box = intersection.combine().objects[0].BoundingBox()
                content_width = sorted(
                    (content_width, intersection_box.xlen + self.padding + qr_box.xlen)
                )[1]
                content_height = sorted((content_height, qr_box.ylen))[1]
            else:
                content_width = qr_box.xlen
                content_height = qr_box.ylen
            content = content.add(
                qr.translate(
                    (content_width - qr_box.xlen, -(content_height - qr_box.ylen), 0)
                )
            )

        sign_width = sorted(
            (self.min_width, self.padding + content_width + self.padding)
        )[1]
        sign_height = sorted(
            (self.min_height, self.padding + content_height + self.padding)
        )[1]

        if sign_width > self.max_width and self.max_width > 0:
            raise ValueError(
                f"Contend width too large\n{sign_width} > {self.max_width}"
            )
        if sign_height > self.max_height and self.max_height > 0:
            raise ValueError(
                f"Contend height too large\n{sign_height} > {self.max_height}"
            )

        background = self.generate_background(sign_width, sign_height, self.thickness)
        border = self.generate_border(sign_width, sign_height, self.border_thickness)
        if len(self.content.text) > 0 and self.start_mark:
            background = background.cut(
                self.generate_start_mark(self.text_start_mark_size)
                .translate(text_pos)
                .translate((0, -(self.padding + self.font_size / 2), 0))
            )
            border = border.cut(
                self.generate_start_mark(self.text_start_mark_size)
                .translate(text_pos)
                .translate((0, -(self.padding + self.font_size / 2), 0))
            )
        if len(self.content.braille) > 0 and self.start_mark:
            background = background.cut(
                self.generate_start_mark(self.braille_start_mark_size)
                .translate(braille_pos)
                .translate((0, -(self.padding + Braille.intercell / 2), 0))
            )
            border = border.cut(
                self.generate_start_mark(self.braille_start_mark_size)
                .translate(braille_pos)
                .translate((0, -(self.padding + Braille.intercell / 2), 0))
            )
        a = cq.Assembly()
        a.add(background, name="background", color=cq.Color("gray4"))
        a.add(
            border.translate((0, 0, (self.thickness + self.border_thickness) / 2)),
            name="border",
            color=cq.Color("white"),
        )
        a.add(
            content.translate((self.padding, -self.padding, self.thickness / 2)),
            name="content",
            color=cq.Color("white"),
        )
        return a
