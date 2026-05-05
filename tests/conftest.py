"""Shared pytest fixtures."""

import numpy as np
import pytest

from src.models import TextBlock


@pytest.fixture
def sample_blocks() -> list[TextBlock]:
    """Synthetic OCR output for an Indonesian receipt."""
    return [
        TextBlock(text="INDOMARET PLUS", confidence=0.98, bbox=[[10, 10], [200, 10], [200, 30], [10, 30]]),
        TextBlock(text="JL. SUDIRMAN NO 1", confidence=0.92, bbox=[[10, 35], [200, 35], [200, 55], [10, 55]]),
        TextBlock(text="04/05/2026 14:30", confidence=0.95, bbox=[[10, 60], [200, 60], [200, 80], [10, 80]]),
        TextBlock(text="Indomie Goreng x2 7,500", confidence=0.88, bbox=[[10, 100], [300, 100], [300, 120], [10, 120]]),
        TextBlock(text="Aqua 600ml 5,000", confidence=0.91, bbox=[[10, 125], [300, 125], [300, 145], [10, 145]]),
        TextBlock(text="Subtotal 12,500", confidence=0.94, bbox=[[10, 200], [300, 200], [300, 220], [10, 220]]),
        TextBlock(text="PPN 11% 1,375", confidence=0.93, bbox=[[10, 225], [300, 225], [300, 245], [10, 245]]),
        TextBlock(text="Total Rp 13,875", confidence=0.97, bbox=[[10, 250], [300, 250], [300, 270], [10, 270]]),
        TextBlock(text="Tunai", confidence=0.96, bbox=[[10, 290], [100, 290], [100, 310], [10, 310]]),
    ]


@pytest.fixture
def fake_image() -> np.ndarray:
    """Plain white image for fake validation tests."""
    return (np.ones((800, 600, 3), dtype=np.uint8) * 255)
