import math
import cadquery2 as cq
import warnings
from cadquery2 import Workplane, Vector, Location
from typing import List, Union, Optional, Literal
from dataclasses import dataclass


BOTTOM_THICKNESS = 2

Divisions = List[Union[List[float], int]]


class IncorrectNumberOfRowsError(Exception):
    pass


class InvalidPropertyError(Exception):
    pass


class SmallDimensionsWarning(Warning):
    pass


class CannotDrawLabelLedgesWarning(Warning):
    pass


@dataclass
class GridfinityDimension:
    x: int
    y: int
    z: int

    @property
    def x_mm(self):
        return self.x * 42 - 0.5

    @property
    def y_mm(self):
        return self.y * 42 - 0.5

    @property
    def z_mm(self):
        return self.z * 7 - 5.6

    def __post_init__(self):
        if self.x < 1 or self.y < 1:
            raise InvalidPropertyError('Width or length cannot be less than 1.')
        if self.z < 2:
            raise InvalidPropertyError('Units high cannot be less than 2.')


@dataclass
class Properties:
    dimension: GridfinityDimension
    divisions: Divisions

    draw_finger_scoop: bool
    draw_label_ledge: bool
    make_magnet_hole: bool
    make_screw_hole: bool

    def __post_init__(self):
        if len(self.divisions) != self.dimension.y:
            raise IncorrectNumberOfRowsError(
                'Number of rows in divisions array must be equal to the number of units long.'
            )


def draw_bases(self: Workplane, dimension: GridfinityDimension) -> Workplane:
    return (
        self
        .rarray(42, 42, dimension.x, dimension.y)
        .eachpoint(lambda loc: (
            cq.Workplane()
            .drawBase()
            .val().located(loc)
        ))
    )


def draw_base(
    self: Workplane
) -> Workplane:
    return (
        self
        .box(36.7, 36.7, 2.6, (True, True, False))
        .edges('|Z').fillet(1.6)
        .faces('<Z').chamfer(0.8)
        .faces('>Z')
        .box(41.5, 41.5, 2.4, (True, True, False))
        .edges('|Z and (>Y or <Y)').fillet(3.75)
        .faces('>>Z[-2]').edges('<Z').chamfer(2.4-0.000001)
    )


def draw_buckets(self: Workplane, dimension: GridfinityDimension, divisions: Divisions) -> Workplane:
    is_drawer_too_small = False
    small_drawer_width = 15

    sketches = []
    x_origin, y_origin = (1, 1)
    for row in divisions:
        if isinstance(row, int):
            row = [1] * row
        buckets_x = [round(ratio / sum(row) * (dimension.x_mm - (len(row) + 1)*0.8), 2)
                  for ratio in row]
        number_of_y_walls = (dimension.y + 1)
        bucket_y = (dimension.y_mm - number_of_y_walls * 0.8) / dimension.y

        for bucket_x in buckets_x:
            if bucket_x < small_drawer_width:
                is_drawer_too_small = True
            sketch = (
                cq.Sketch()
                .rect(bucket_x, bucket_y)
                .vertices()
                .fillet(3.75 - 0.4)
                .edges()
                .moved(Location(Vector(
                    bucket_x / 2,
                    -bucket_y / 2
                )))
                .moved(Location(Vector(
                    -dimension.x_mm / 2 + x_origin,
                    dimension.y_mm / 2 - y_origin
                )))
            )
            x_origin = x_origin + bucket_x + 0.8
            sketches.append(sketch)
        x_origin = 1
        y_origin = y_origin + bucket_y + 0.8

    if is_drawer_too_small:
        warnings.warn(
            f'Drawer width is less than or equal to {small_drawer_width}mm',
            SmallDimensionsWarning
        )

    return (
        self
        .faces('<Z[0]').workplane(centerOption='CenterOfBoundBox').tag('base')
        .box(dimension.x_mm, dimension.y_mm, dimension.z_mm, (True, True, False))
        .edges('|Z').fillet(3.75)
        .faces('>Z')
        .workplane()
        .placeSketch(*sketches)
        .extrude(BOTTOM_THICKNESS - dimension.z_mm, 'cut')
    )


def draw_mate2(self: Workplane, dimension: GridfinityDimension) -> Workplane:
    height = 2.4 + 1 + 1.6

    top = (
        cq.Workplane().copyWorkplane(
            self.workplaneFromTagged('base')
            .workplane(offset=dimension.z_mm + 0.0001)
        )
        .box(dimension.x_mm, dimension.y_mm, height, (True, True, False))
        .edges('|Z').fillet(3.75)
        .faces('>Z').sketch()
        .rect(dimension.x_mm - 2 * 2.4, dimension.y_mm - 2 * 2.4)
        .vertices().fillet(3.75 - 2.4).finalize().cutThruAll()
        .faces('>Z').sketch()
        .rect(dimension.x_mm, dimension.y_mm)
        .vertices().fillet(3.75).finalize().cutThruAll(taper=45)
        .faces('<Z').sketch()
        .rect(dimension.x_mm - 2 * 0.8, dimension.y_mm - 2 * 0.8)
        .vertices().fillet(3.75).finalize().cutThruAll(taper=-45)
    )
    return self.union(top)


def draw_mate(self: Workplane, dimension: GridfinityDimension) -> Workplane:

    width = dimension.x_mm
    length = dimension.y_mm
    outer_fillet = 3.75

    s1 = (
        cq.Sketch()
        .rect(width, length)
        .vertices().fillet(outer_fillet)
    )

    s2 = (
        cq.Sketch()
        .rect(width - 1.9 * 2, length - 1.9 * 2)
        .vertices().fillet(outer_fillet - 1.9)
    )

    s3 = (
        cq.Sketch()
        .rect(width - 2.6 * 2, length - 2.6 * 2)
        .vertices().fillet(outer_fillet - 2.6)
    )

    s4 = (
        cq.Sketch()
        .rect(width - 0.8 * 2, length - 0.8 * 2)
        .vertices().fillet(outer_fillet - 1)
    )

    top = (
        cq.Workplane().copyWorkplane(
            self.workplaneFromTagged('base')
            .workplane(offset=dimension.z_mm - 2.84)
        )
        .box(width, length, 7.24, (True, True, False))
        .edges('|Z').fillet(outer_fillet)
        .faces('>Z')
        .placeSketch(
            s1,
            s2.moved(Location(Vector(0, 0, -1.9))),
            s2.moved(Location(Vector(0, 0, -3.7))),
            s3.moved(Location(Vector(0, 0, -4.4))),
            s3.moved(Location(Vector(0, 0, -5.6))),
            s4.moved(Location(Vector(0, 0, -7.24)))
        )
        .loft(True, 's')
    )

    return self.union(top)


def draw_finger_scoops(self: Workplane, dimension: GridfinityDimension) -> Workplane:
    bucket_length = (dimension.y_mm - (dimension.y + 1)*0.8) / dimension.y
    scoop_radius = min(dimension.z_mm * 0.3, bucket_length * 0.9)

    sketches = []
    for i in range(0, dimension.y):
        sketch = (
            cq.Sketch()
            .rect(scoop_radius, scoop_radius)
            .vertices('>X and >Y')
            .circle(scoop_radius, mode='s')
            .moved(Location(Vector(
                scoop_radius / 2 -
                0.5 * bucket_length * dimension.y -
                math.floor(dimension.y / 2) +
                (0.5 if dimension.y % 2 == 0 else 0),
                scoop_radius / 2 - (dimension.z_mm - BOTTOM_THICKNESS) / 2)))
            .moved(Location(Vector(
                i * (bucket_length + 1) + (1.6 if i == 0 else 0),
                0
            )))
        )
        sketches.append(sketch)

    return (
        self.faces('>X[1]')
        .workplane(centerOption='CenterOfBoundBox')
        .placeSketch(*sketches)
        .extrude(dimension.x_mm - 0.8)
    )


def draw_label_ledge(self: Workplane, dimension: GridfinityDimension) -> Workplane:
    bucket_length = (dimension.y_mm - (dimension.y + 1)) / dimension.y
    ledge_length = 12 + 0.75
    back_ledge_offset = 2.9

    max_ledge_height = dimension.z_mm - BOTTOM_THICKNESS

    last_offset = 0
    ledge_height = min(max_ledge_height, ledge_length)

    sketches = []
    for i in range(0, dimension.y):

        if i == dimension.y - 1:
            last_offset = back_ledge_offset
            ledge_height = min(max_ledge_height, ledge_length + last_offset)

        sketch = (
            cq.Sketch()
            .segment((last_offset, -ledge_height), (last_offset, 0))
            .segment((-ledge_length, 0))
        )

        if ledge_height < ledge_length:
            sketch = sketch.segment(
                (-ledge_length + ledge_height, -ledge_height))

        sketch = (
            sketch
            .close()
            .assemble()
            .vertices('<X')
            .fillet(0.6)
            .moved(Location(Vector(
                - 0.5 - (0.5 * dimension.y - 1) * (bucket_length + 1),
                (dimension.z_mm - BOTTOM_THICKNESS) / 2)))
            .moved(Location(Vector(
                i * (bucket_length + 1) - last_offset,
                0
            )))
        )
        sketches.append(sketch)

    return (
        self.faces('>X[1]')
        .workplane(centerOption='CenterOfBoundBox')
        .placeSketch(*sketches)
        .extrude(dimension.x_mm - 1.5)
    )


def draw_magnet_holes(self: Workplane) -> Workplane:
    self.plane.zDir = Vector(0, 0, -1)

    self = (
        self
        .faces('<Z[-1]')
        .faces(cq.selectors.AreaNthSelector(-1))
        .rect(26, 26, forConstruction=True)
        .vertices()
    )

    return self.hole(6.5, 2.4)


def draw_screw_holes(self: Workplane) -> Workplane:
    self.plane.zDir = Vector(0, 0, -1)

    self = (
        self
        .faces('<Z[-1]')
        .faces(cq.selectors.AreaNthSelector(-1))
        .rect(26, 26, forConstruction=True)
        .vertices()
    )

    return self.cboreHole(3, 6.5, 2.4, 6)


Workplane.drawBase = draw_base
Workplane.drawBases = draw_bases
Workplane.drawBuckets = draw_buckets
Workplane.drawMate = draw_mate
Workplane.drawFingerScoops = draw_finger_scoops
Workplane.drawLabelLedge = draw_label_ledge
Workplane.drawMagnetHoles = draw_magnet_holes
Workplane.drawScrewHoles = draw_screw_holes


def make_box(
    prop: Properties,
    out_file: Union[str, None] = None,
    export_type: Optional[Literal['STL', 'STEP', 'AMF',
                                  'SVG', 'TJS', 'DXF', 'VRML', 'VTP']] = None,
    tolerance: float = 0.1,
    angular_tolerance: float = 0.1,
    opt=None
) -> Workplane:
    box = make_gridfinity_box(cq.Workplane(), prop)

    if out_file:
        export_box(
            box,
            out_file=out_file,
            export_type=export_type,
            tolerance=tolerance,
            angular_tolerance=angular_tolerance,
            opt=opt
        )
    return box


def make_gridfinity_box(wp: Workplane, prop: Properties):
    wp = (
        wp
        .drawBases(prop.dimension)
        .drawBuckets(prop.dimension, prop.divisions)
    )
    if prop.draw_finger_scoop:
        wp = wp.drawFingerScoops(prop.dimension)
    if prop.draw_label_ledge:
        wp = wp.drawLabelLedge(prop.dimension)
    wp = wp.drawMate(prop.dimension)
    if prop.make_magnet_hole:
        wp = wp.drawMagnetHoles()
    if prop.make_screw_hole:
        wp = wp.drawScrewHoles()

    return wp


def export_box(
    box: Workplane,
    out_file: Union[str, None] = None,
    export_type: Optional[Literal['STL', 'STEP', 'AMF',
                                  'SVG', 'TJS', 'DXF', 'VRML', 'VTP']] = None,
    tolerance: float = 0.1,
    angular_tolerance: float = 0.1,
    opt=None
) -> Workplane:
    cq.exporters.export(
        box,
        out_file,
        exportType=export_type,
        tolerance=tolerance,
        angularTolerance=angular_tolerance,
        opt=opt
    )
    return box


def export_svg(
    box: Workplane,
    out_file: Union[str, None] = None,
    opt=None
) -> Workplane:

    settings = {
        'showAxes': False,
        'marginLeft': 10,
        'marginTop': 10,
        'projectionDir': (2.75, -2.6, 2),
        'showHidden': False,
        'focus': 500
    }
    if opt:
        settings.update(opt)

    export_box(
        box,
        out_file=out_file,
        export_type='SVG',
        opt=settings
    )

    return box
