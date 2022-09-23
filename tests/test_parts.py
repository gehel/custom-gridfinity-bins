import unittest

import cadquery2 as cq
import inspect

from cadquery2 import Workplane

from gridfinity import draw_base, draw_bases, draw_buckets, draw_finger_scoops, draw_front_surface, draw_label_ledge, \
    draw_magnet_holes, draw_mate, draw_screw_holes, GridfinityDimension, \
    make_gridfinity_box, Properties, shave_outer_shell


class MyTestCase(unittest.TestCase):
    """
    Generates SVG and STL files for the various intermediate operations. Those are expected to be validated
    manually, no assertions are made during these tests.
    """
    properties = Properties(
        GridfinityDimension(2, 3, 4),
        [1, 1, 1],
        True,
        True,
        False,
        True)

    def test_draw_bases(self):
        wp = cq.Workplane()
        wp = draw_bases(wp, self.properties.dimension)
        export_for_testing(wp)

    def test_draw_base(self):
        wp = cq.Workplane()
        wp = draw_base(wp)
        export_for_testing(wp)

    def test_draw_buckets(self):
        wp = cq.Workplane()
        wp = wp.box(self.properties.dimension.x_mm, self.properties.dimension.y_mm, 30)
        wp = draw_buckets(wp, self.properties.dimension, self.properties.divisions)
        export_for_testing(wp)

    def test_draw_front_surface(self):
        # TODO: not really sure what this front surface is about
        wp = cq.Workplane()
        wp = draw_bases(wp, self.properties.dimension)
        wp = draw_buckets(wp, self.properties.dimension, self.properties.divisions)
        wp = draw_front_surface(wp, self.properties.dimension)
        export_for_testing(wp)

    def test_draw_finger_scoops(self):
        wp = cq.Workplane()
        wp = wp.box(1, self.properties.dimension.y_mm, self.properties.dimension.z_mm)
        wp = draw_finger_scoops(wp, self.properties.dimension)
        export_for_testing(wp)

    def test_draw_label_ledge(self):
        wp = cq.Workplane()
        wp = wp.box(1, self.properties.dimension.y_mm, self.properties.dimension.z_mm)
        wp = draw_label_ledge(wp, self.properties.dimension)
        export_for_testing(wp)

    def test_draw_mate(self):
        wp = cq.Workplane()
        wp = wp.box(self.properties.dimension.x_mm, self.properties.dimension.y_mm, 1) \
            .faces("<Z[0]") \
            .tag('base')
        wp = draw_mate(wp, self.properties.dimension)
        export_for_testing(wp)

    def test_draw_magnet_holes(self):
        wp = cq.Workplane()
        wp = wp.box(self.properties.dimension.x_mm, self.properties.dimension.y_mm, 5)
        wp = draw_magnet_holes(wp)
        export_for_testing(wp)

    def test_draw_screw_holes(self):
        wp = cq.Workplane()
        wp = wp.box(self.properties.dimension.x_mm, self.properties.dimension.y_mm, 5)
        wp = draw_screw_holes(wp)
        export_for_testing(wp)

    def test_shave_outer_shell(self):
        wp = cq.Workplane()
        wp = wp.box(self.properties.dimension.x_mm, self.properties.dimension.y_mm, self.properties.dimension.z_mm)
        wp = shave_outer_shell(wp, self.properties.dimension)
        wp = wp.box(self.properties.dimension.x_mm, self.properties.dimension.y_mm, self.properties.dimension.z_mm/2)
        export_for_testing(wp)

    def test_make_gridfinity_box(self):
        wp = cq.Workplane()
        wp = make_gridfinity_box(wp, self.properties)
        export_for_testing(wp)


def export_for_testing(wp: Workplane) -> None:
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
            "showAxes": False,
            "marginLeft": 10,
            "marginTop": 10,
            "projectionDir": (2.75, -2.6, 2),
            "showHidden": False,
            "focus": 500
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
