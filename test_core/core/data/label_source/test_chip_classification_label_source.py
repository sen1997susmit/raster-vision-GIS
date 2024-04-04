import unittest
import os

import geopandas as gpd

from rastervision.pipeline.file_system import json_to_file, get_tmp_dir
from rastervision.core.box import Box
from rastervision.core.data import (
    ClassConfig, ChipClassificationLabelSourceConfig,
    GeoJSONVectorSourceConfig, ClassInferenceTransformerConfig,
    BufferTransformerConfig)
from rastervision.core.data.label_source.chip_classification_label_source \
    import infer_cells

from tests import data_file_path
from tests.core.data.mock_crs_transformer import DoubleCRSTransformer


class TestChipClassificationLabelSourceConfig(unittest.TestCase):
    def test_ensure_required_transformers(self):
        uri = data_file_path('bboxes.geojson')
        cfg = ChipClassificationLabelSourceConfig(
            vector_source=GeoJSONVectorSourceConfig(uris=uri))
        tfs = cfg.vector_source.transformers
        has_inf_tf = any(
            isinstance(tf, ClassInferenceTransformerConfig) for tf in tfs)
        has_buf_tf = any(isinstance(tf, BufferTransformerConfig) for tf in tfs)
        self.assertTrue(has_inf_tf)
        self.assertTrue(has_buf_tf)


class TestChipClassificationLabelSource(unittest.TestCase):
    def setUp(self):
        self.crs_transformer = DoubleCRSTransformer()
        self.geojson = {
            'type':
            'FeatureCollection',
            'features': [{
                'type': 'Feature',
                'geometry': {
                    'type':
                    'MultiPolygon',
                    'coordinates': [[[[0., 0.], [0., 2.], [2., 2.], [2., 0.],
                                      [0., 0.]]]]
                },
                'properties': {
                    'class_name': 'car',
                    'class_id': 0,
                    'score': 0.0
                }
            }, {
                'type': 'Feature',
                'geometry': {
                    'type':
                    'Polygon',
                    'coordinates': [[[2., 2.], [2., 4.], [4., 4.], [4., 2.],
                                     [2., 2.]]]
                },
                'properties': {
                    'score': 0.0,
                    'class_name': 'house',
                    'class_id': 1
                }
            }]
        }

        self.class_config = ClassConfig(names=['car', 'house'])

        self.box1 = Box.make_square(0, 0, 4)
        self.box2 = Box.make_square(4, 4, 4)
        self.class_id1 = 0
        self.class_id2 = 1
        self.background_class_id = 2

        self.labels_df = gpd.GeoDataFrame.from_features(self.geojson)

        self.file_name = 'labels.json'
        self.tmp_dir = get_tmp_dir()
        self.uri = os.path.join(self.tmp_dir.name, self.file_name)
        json_to_file(self.geojson, self.uri)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_infer_cell1(self):
        # More of box 1 is in cell.
        cell = Box.make_square(0, 0, 3)
        ioa_thresh = 0.5
        use_intersection_over_cell = False
        background_class_id = self.background_class_id
        pick_min_class_id = False

        labels = infer_cells(
            [cell],
            self.labels_df,
            ioa_thresh=ioa_thresh,
            use_intersection_over_cell=use_intersection_over_cell,
            background_class_id=background_class_id,
            pick_min_class_id=pick_min_class_id)
        class_id = labels.get_cell_class_id(cell)
        self.assertEqual(class_id, self.class_id1)

    def test_infer_cell2(self):
        # More of box 2 is in cell.
        cell = Box.make_square(1, 1, 3)
        ioa_thresh = 0.5
        use_intersection_over_cell = False
        background_class_id = self.background_class_id
        pick_min_class_id = False

        labels = infer_cells(
            [cell],
            self.labels_df,
            ioa_thresh=ioa_thresh,
            use_intersection_over_cell=use_intersection_over_cell,
            background_class_id=background_class_id,
            pick_min_class_id=pick_min_class_id)
        class_id = labels.get_cell_class_id(cell)
        self.assertEqual(class_id, self.class_id2)

    def test_infer_cell3(self):
        # Only box 2 is in cell, but IOA isn't high enough.
        cell = Box.make_square(3, 3, 3)
        ioa_thresh = 0.5
        use_intersection_over_cell = False
        background_class_id = self.background_class_id
        pick_min_class_id = False

        labels = infer_cells(
            [cell],
            self.labels_df,
            ioa_thresh=ioa_thresh,
            use_intersection_over_cell=use_intersection_over_cell,
            background_class_id=background_class_id,
            pick_min_class_id=pick_min_class_id)
        class_id = labels.get_cell_class_id(cell)
        self.assertEqual(class_id, background_class_id)

    def test_infer_cell4(self):
        # Both boxes inside cell, but using intersection_over_cell,
        # the IOA isn't high enough.
        cell = Box.make_square(0, 0, 10)
        ioa_thresh = 0.5
        use_intersection_over_cell = True
        background_class_id = self.background_class_id
        pick_min_class_id = False

        labels = infer_cells(
            [cell],
            self.labels_df,
            ioa_thresh=ioa_thresh,
            use_intersection_over_cell=use_intersection_over_cell,
            background_class_id=background_class_id,
            pick_min_class_id=pick_min_class_id)
        class_id = labels.get_cell_class_id(cell)
        self.assertEqual(class_id, background_class_id)

    def test_infer_cell5(self):
        # More of box1 in cell, using intersection_over_cell with the
        # IOA high enough.
        cell = Box.make_square(0, 0, 3)
        ioa_thresh = 0.4
        use_intersection_over_cell = True
        background_class_id = self.background_class_id
        pick_min_class_id = False

        labels = infer_cells(
            [cell],
            self.labels_df,
            ioa_thresh=ioa_thresh,
            use_intersection_over_cell=use_intersection_over_cell,
            background_class_id=background_class_id,
            pick_min_class_id=pick_min_class_id)
        class_id = labels.get_cell_class_id(cell)
        self.assertEqual(class_id, self.class_id1)

    def test_infer_cell6(self):
        # No boxes overlap enough, use background_class_id
        cell = Box.make_square(0, 0, 10)
        ioa_thresh = 0.5
        use_intersection_over_cell = True
        background_class_id = self.background_class_id
        pick_min_class_id = False

        labels = infer_cells(
            [cell],
            self.labels_df,
            ioa_thresh=ioa_thresh,
            use_intersection_over_cell=use_intersection_over_cell,
            background_class_id=background_class_id,
            pick_min_class_id=pick_min_class_id)
        class_id = labels.get_cell_class_id(cell)
        self.assertEqual(class_id, self.background_class_id)

    def test_infer_cell7(self):
        # Cell doesn't overlap with any boxes.
        cell = Box.make_square(10, 10, 1)
        ioa_thresh = 0.5
        use_intersection_over_cell = True
        background_class_id = self.background_class_id
        pick_min_class_id = False

        labels = infer_cells(
            [cell],
            self.labels_df,
            ioa_thresh=ioa_thresh,
            use_intersection_over_cell=use_intersection_over_cell,
            background_class_id=background_class_id,
            pick_min_class_id=pick_min_class_id)
        class_id = labels.get_cell_class_id(cell)
        self.assertEqual(class_id, background_class_id)

    def test_infer_cell8(self):
        # box2 overlaps more than box1, but using pick_min_class_id, so
        # picks box1.
        cell = Box.make_square(1, 1, 3)
        ioa_thresh = 0.5
        use_intersection_over_cell = False
        background_class_id = self.background_class_id
        pick_min_class_id = True

        labels = infer_cells(
            [cell],
            self.labels_df,
            ioa_thresh=ioa_thresh,
            use_intersection_over_cell=use_intersection_over_cell,
            background_class_id=background_class_id,
            pick_min_class_id=pick_min_class_id)
        class_id = labels.get_cell_class_id(cell)
        self.assertEqual(class_id, self.class_id2)

    def test_get_labels_inferred(self):
        extent = Box.make_square(0, 0, 8)

        config = ChipClassificationLabelSourceConfig(
            vector_source=GeoJSONVectorSourceConfig(uris=self.uri),
            ioa_thresh=0.5,
            use_intersection_over_cell=False,
            pick_min_class_id=False,
            background_class_id=self.background_class_id,
            infer_cells=True,
            cell_sz=4)
        source = config.build(self.class_config, self.crs_transformer, extent,
                              self.tmp_dir.name)
        labels = source.get_labels()
        cells = labels.get_cells()

        self.assertEqual(len(cells), 4)
        self.assertEqual(labels.get_cell_class_id(self.box1), self.class_id1)
        self.assertEqual(labels.get_cell_class_id(self.box2), self.class_id2)
        self.assertEqual(
            labels.get_cell_class_id(Box.make_square(0, 4, 4)),
            self.background_class_id)
        self.assertEqual(
            labels.get_cell_class_id(Box.make_square(4, 0, 4)),
            self.background_class_id)

    def test_get_labels_small_extent(self):
        # Extent only has enough of first box in it.
        extent = Box.make_square(0, 0, 2)

        config = ChipClassificationLabelSourceConfig(
            vector_source=GeoJSONVectorSourceConfig(uris=self.uri))
        source = config.build(self.class_config, self.crs_transformer, extent,
                              self.tmp_dir.name)
        labels = source.get_labels()

        cells = labels.get_cells()
        self.assertEqual(len(cells), 1)
        class_id = labels.get_cell_class_id(self.box1)
        self.assertEqual(class_id, self.class_id1)
        class_id = labels.get_cell_class_id(self.box2)
        self.assertEqual(class_id, None)

    def test_get_labels(self):
        # Extent contains both boxes.
        extent = Box.make_square(0, 0, 8)

        config = ChipClassificationLabelSourceConfig(
            vector_source=GeoJSONVectorSourceConfig(uris=self.uri))
        source = config.build(self.class_config, self.crs_transformer, extent,
                              self.tmp_dir.name)
        labels = source.get_labels()

        cells = labels.get_cells()
        self.assertEqual(len(cells), 2)
        class_id = labels.get_cell_class_id(self.box1)
        self.assertEqual(class_id, self.class_id1)
        class_id = labels.get_cell_class_id(self.box2)
        self.assertEqual(class_id, self.class_id2)

    def test_getitem(self):
        # Extent contains both boxes.
        extent = Box.make_square(0, 0, 8)

        config = ChipClassificationLabelSourceConfig(
            vector_source=GeoJSONVectorSourceConfig(uris=self.uri))
        source = config.build(self.class_config, self.crs_transformer, extent,
                              self.tmp_dir.name)
        labels = source.get_labels()

        cells = labels.get_cells()
        self.assertEqual(len(cells), 2)
        self.assertEqual(source[cells[0]], self.class_id1)
        self.assertEqual(source[cells[1]], self.class_id2)


if __name__ == '__main__':
    unittest.main()
