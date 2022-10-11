import unittest
from typing import Optional

import cadquery2 as cq
import inspect

from cadquery2 import Workplane

from gridfinity import draw_base, draw_bases, draw_bucket_sketch, draw_buckets, draw_finger_scoops, draw_label_ledge, \
    draw_magnet_holes, draw_mate, draw_screw_holes, GridfinityDimension, \
    make_gridfinity_box, Properties


class GridfinityDimensionTests(unittest.TestCase):

    def test_str(self):
        self.assertEqual(
            GridfinityDimension(2, 3, 4).__str__(),
            '2x3x4'
        )


class PropertiesTests(unittest.TestCase):

    properties = Properties(
        GridfinityDimension(2, 3, 4),
        [1, 2, [2, 1]],
        0.8,
        True,
        True,
        False,
        True)

    def test_str(self):
        self.assertEqual(
            self.properties.__str__(),
            'gridfinity_bin_2x3x4_0.8_with-finger_scoop_with-label-ledge_with-screw-holes'
        )


class MyTestCase(unittest.TestCase):
    """
    Generates SVG and STL files for the various intermediate operations. Those are expected to be validated
    manually, no assertions are made during these tests.
    """
    properties = Properties(
        GridfinityDimension(2, 3, 4),
        [1, 2, [2, 1]],
        0.8,
        True,
        True,
        False,
        True)

    def test_draw_bases(self):
        wp = cq.Workplane()
        wp = draw_bases(wp, self.properties.dimension, self.properties.make_magnet_hole)
        export_for_testing(wp)

    def test_draw_bases_with_magnet_holes(self):
        wp = cq.Workplane()
        wp = draw_bases(wp, self.properties.dimension, True)
        export_for_testing(wp)

    def test_draw_base(self):
        wp = cq.Workplane()
        wp = draw_base(wp, self.properties.make_magnet_hole)
        export_for_testing(wp)

    def test_draw_bucket_sketch(self):
        wp = cq.Workplane()
        wp = wp.box(100, 200, 1)

        buckets = []

        bucket = draw_bucket_sketch(
            x_mm=94, y_mm=95.5,
            support_x_mm=100, support_y_mm=200,
            x_origin=3, y_origin=3,
            wall_thickness=3, small_drawer_width=16
        )
        buckets.append(bucket)

        bucket = draw_bucket_sketch(
            x_mm=94, y_mm=95.5,
            support_x_mm=100, support_y_mm=200,
            x_origin=3, y_origin=3 + 95.5 + 3,
            wall_thickness=3, small_drawer_width=16
        )
        buckets.append(bucket)

        wp = wp.placeSketch(*buckets).cutThruAll()
        export_for_testing(wp)

    def test_draw_buckets(self):
        wp = cq.Workplane()
        wp = wp.box(self.properties.dimension.x_mm, self.properties.dimension.y_mm, 5.6)
        wp = draw_buckets(wp, self.properties.dimension, self.properties.divisions, self.properties.wall_thickness)
        export_for_testing(wp)

    def test_draw_buckets_thick_walls(self):
        wp = cq.Workplane()
        wp = wp.box(self.properties.dimension.x_mm, self.properties.dimension.y_mm, 5.6)
        wp = draw_buckets(wp, self.properties.dimension, [[3, 4], 5, [2, 1]], 3)
        export_for_testing(wp)

    def test_draw_up_to_buckets(self):
        wp = cq.Workplane()
        wp = draw_bases(wp, self.properties.dimension, self.properties.make_magnet_hole)
        wp = draw_buckets(wp, self.properties.dimension, self.properties.divisions, self.properties.wall_thickness)
        export_for_testing(wp)

    def test_draw_finger_scoops(self):
        wp = cq.Workplane()
        wp = wp.box(1, self.properties.dimension.y_mm, self.properties.dimension.z_mm)
        wp = draw_finger_scoops(wp, self.properties.dimension)
        export_for_testing(wp)

    def test_draw_up_to_finger_scoops(self):
        wp = cq.Workplane()
        wp = draw_bases(wp, self.properties.dimension, self.properties.make_magnet_hole)
        wp = draw_buckets(wp, self.properties.dimension, self.properties.divisions, self.properties.wall_thickness)
        wp = draw_finger_scoops(wp, self.properties.dimension)
        export_for_testing(wp)

    def test_draw_label_ledge(self):
        wp = cq.Workplane()
        wp = wp.box(1, self.properties.dimension.y_mm, self.properties.dimension.z_mm)
        wp = draw_label_ledge(wp, self.properties.dimension, self.properties.wall_thickness)
        export_for_testing(wp)

    def test_draw_up_to_label_ledge(self):
        wp = cq.Workplane()
        wp = draw_bases(wp, self.properties.dimension, self.properties.make_magnet_hole)
        wp = draw_buckets(wp, self.properties.dimension, self.properties.divisions, self.properties.wall_thickness)
        wp = draw_label_ledge(wp, self.properties.dimension, self.properties.wall_thickness)
        export_for_testing(wp)

    def test_draw_mate(self):
        wp = cq.Workplane()
        wp = wp.box(self.properties.dimension.x_mm, self.properties.dimension.y_mm, 1).faces('<Z[0]').tag('base')
        wp = draw_mate(wp, self.properties.dimension)
        export_for_testing(wp)

    def test_draw_up_to_mate(self):
        wp = cq.Workplane()
        wp = draw_bases(wp, self.properties.dimension, self.properties.make_magnet_hole)
        wp = draw_buckets(wp, self.properties.dimension, self.properties.divisions, self.properties.wall_thickness)
        wp = draw_mate(wp, self.properties.dimension)
        export_for_testing(wp)

    def test_draw_magnet_holes(self):
        wp = cq.Workplane()
        wp = wp.box(self.properties.dimension.x_mm, self.properties.dimension.y_mm, 5)
        wp = draw_magnet_holes(wp)
        export_for_testing(wp)

    def test_draw_up_to_magnet_holes(self):
        wp = cq.Workplane()
        wp = draw_bases(wp, self.properties.dimension, self.properties.make_magnet_hole)
        wp = draw_buckets(wp, self.properties.dimension, self.properties.divisions, self.properties.wall_thickness)
        wp = draw_magnet_holes(wp)
        export_for_testing(wp)

    def test_draw_screw_holes(self):
        wp = cq.Workplane()
        wp = wp.box(self.properties.dimension.x_mm, self.properties.dimension.y_mm, 5)
        wp = draw_screw_holes(wp)
        export_for_testing(wp)

    def test_make_gridfinity_box(self):
        wp = cq.Workplane()
        wp = make_gridfinity_box(wp, self.properties)
        export_for_testing(wp)

    def test_minimal_box(self):
        dimension = GridfinityDimension(1, 1, 7)
        wp = cq.Workplane()
        wp = draw_bases(wp, dimension, self.properties.make_magnet_hole)
        wp = draw_buckets(wp, dimension, [1], 0.8)
        wp = draw_mate(wp, dimension)
        export_for_testing(wp, 'gridfinity_bin_{dimension.x}x{dimension.y}x{dimension.z}'.format(dimension=dimension))


def export_for_testing(wp: Workplane, name: Optional[str] = None) -> None:
    if name is None:
        name = inspect.getframeinfo(inspect.currentframe().f_back).function
    export_svg(wp, name)
    export_stl(wp, name)


def export_svg(wp: Workplane, name: str) -> None:
    cq.exporters.export(
        wp,
        '%s.svg' % name,
        exportType='SVG',
        tolerance=0.1,
        angularTolerance=0.1,
        opt={
            'showAxes': False,
            'marginLeft': 10,
            'marginTop': 10,
            'projectionDir': (2.75, -2.6, 2),
            'showHidden': False,
            'focus': 500
        })


def export_stl(wp: Workplane, name: str) -> None:
    cq.exporters.export(
        wp,
        '%s.stl' % name,
        exportType='STL',
        tolerance=0.1,
        angularTolerance=0.1,
    )


if __name__ == '__main__':
    unittest.main()
