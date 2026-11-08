import pytest

from anylabeling.views.labeling.utils.filename_label import (
    plant_label_from_filename,
)


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("Maize_F12_21_003_rgb.png", "maize"),
        ("sugarbeet_north_7_120_rgb.png", "sugarbeet"),
        ("WHEAT_field_A_35_001_RGB.PNG", "wheat"),
        (r"C:\data\images\Soy_F1_14_002_rgb.png", "soy"),
        ("/data/images/Soy_F1_14_002_rgb.png", "soy"),
        ("Čičerika_F1_14_002_rgb.png", "cicerika"),
        ("šparglji_F1_14_002_rgb.png", "sparglji"),
        ("ŽITO_F1_14_002_rgb.png", "zito"),
        ("Ćuran_F1_14_002_rgb.png", "curan"),
        ("Đumbir_F1_14_002_rgb.png", "dumbir"),
        # Decomposed (NFD) filename, as macOS may produce.
        ("Žito_F1_14_002_rgb.png", "zito"),
    ],
)
def test_plant_label_from_matching_filename(filename, expected):
    assert plant_label_from_filename(filename) == expected


@pytest.mark.parametrize(
    "filename",
    [
        None,
        "",
        "Maize_F12_21_003.png",
        "Maize_F12_21_003_rgb.jpg",
        "Maize_F12_x_003_rgb.png",
        "Maize_21_003_rgb.png",
        "random_image.png",
    ],
)
def test_plant_label_from_non_matching_filename(filename):
    assert plant_label_from_filename(filename) is None
