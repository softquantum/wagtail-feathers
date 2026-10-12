"""Tests for the wagtail-localize integration of CodeBlock."""

import uuid

import pytest

pytest.importorskip("wagtail_localize")

from wagtail.blocks import StructValue  # noqa: E402
from wagtail.models import Locale  # noqa: E402
from wagtail_localize.segments import OverridableSegmentValue, StringSegmentValue  # noqa: E402
from wagtail_localize.segments.extract import extract_segments  # noqa: E402
from wagtail_localize.segments.ingest import StreamFieldSegmentsWriter  # noqa: E402

from wagtail_feathers.blocks import CodeBlock  # noqa: E402
from wagtail_feathers.models.base import FeatherBasePage  # noqa: E402

SAMPLE_CODE = "def hello():\n    return 'world'\n"


def make_value(block, caption=""):
    """Build a CodeBlock StructValue with the sample code."""
    return block.to_python({"language": "python", "code": SAMPLE_CODE, "caption": caption})


class TestGetTranslatableSegments:
    """CodeBlock exposes code as an overridable segment and caption as a string segment."""

    def test_code_is_single_overridable_segment(self):
        """Without a caption, exactly one overridable segment at path 'code' is produced."""
        block = CodeBlock()
        segments = block.get_translatable_segments(make_value(block))
        assert len(segments) == 1
        segment = segments[0]
        assert isinstance(segment, OverridableSegmentValue)
        assert segment.path == "code"
        assert segment.data == SAMPLE_CODE

    def test_caption_is_string_segment(self):
        """A non-empty caption adds a translatable string segment at path 'caption'."""
        block = CodeBlock()
        segments = block.get_translatable_segments(make_value(block, caption="Example"))
        captions = [s for s in segments if s.path == "caption"]
        assert len(captions) == 1
        assert isinstance(captions[0], StringSegmentValue)
        assert captions[0].render_text() == "Example"
        assert len(segments) == 2

    def test_no_string_segment_for_code(self):
        """The code child never becomes a translatable string segment."""
        block = CodeBlock()
        segments = block.get_translatable_segments(make_value(block, caption="Example"))
        assert not any(isinstance(s, StringSegmentValue) and s.path == "code" for s in segments)

    def test_no_segment_for_language(self):
        """The language child yields no segment at all."""
        block = CodeBlock()
        segments = block.get_translatable_segments(make_value(block, caption="Example"))
        assert all(s.path != "language" for s in segments)


class TestRestoreTranslatedSegments:
    """CodeBlock rebuilds a StructValue from the source value plus incoming segments."""

    def test_override_replaces_code(self):
        """An overridable segment replaces the code child and leaves language untouched."""
        block = CodeBlock()
        source = make_value(block, caption="Example")
        result = block.restore_translated_segments(source, [OverridableSegmentValue("code", "print(1)")])
        assert isinstance(result, StructValue)
        assert result["code"] == "print(1)"
        assert result["language"] == "python"
        assert result["caption"] == "Example"

    def test_translated_caption_only(self):
        """A caption string segment alone replaces the caption and keeps the source code."""
        block = CodeBlock()
        source = make_value(block, caption="Example")
        result = block.restore_translated_segments(source, [StringSegmentValue("caption", "Exemple")])
        assert result["caption"] == "Exemple"
        assert result["code"] == SAMPLE_CODE
        assert result["language"] == "python"

    def test_both_segments(self):
        """Code override and caption translation are applied together."""
        block = CodeBlock()
        source = make_value(block, caption="Example")
        result = block.restore_translated_segments(
            source,
            [OverridableSegmentValue("code", "print(2)"), StringSegmentValue("caption", "Exemple")],
        )
        assert result["code"] == "print(2)"
        assert result["caption"] == "Exemple"

    def test_no_segments_keeps_source(self):
        """With no segments the result equals the source value."""
        block = CodeBlock()
        source = make_value(block, caption="Example")
        result = block.restore_translated_segments(source, [])
        assert dict(result) == dict(source)

    def test_theme_preserved(self):
        """The theme sub-struct is carried over unchanged."""
        block = CodeBlock()
        source = block.to_python(
            {
                "theme": {"theme_variant": "default", "classname": "wide", "style_id": "snippet"},
                "language": "bash",
                "code": "ls -la",
                "caption": "",
            }
        )
        result = block.restore_translated_segments(source, [OverridableSegmentValue("code", "ls")])
        assert result["theme"]["classname"] == "wide"
        assert result["theme"]["style_id"] == "snippet"
        assert result["language"] == "bash"


@pytest.fixture
def body_with_code():
    """Build a FeatherBasePage body StreamValue holding one code block."""
    field = FeatherBasePage._meta.get_field("body")
    return field.to_python(
        [
            {
                "type": "code_block",
                "id": str(uuid.uuid4()),
                "value": {"language": "python", "code": SAMPLE_CODE, "caption": "Greeting"},
            }
        ]
    )


@pytest.mark.django_db
class TestRealExtractorAndWriter:
    """The real wagtail-localize extractor and writer honour the CodeBlock hooks."""

    def test_extractor_produces_no_string_segment_for_code(self, body_with_code):
        """Extracting a page body yields an overridable segment for code and no string segment."""
        from tests.testapp.models import StandardPage

        Locale.objects.get_or_create(language_code="en")
        page = StandardPage(title="Code", body=body_with_code)
        segments = extract_segments(page)

        string_segments = [s for s in segments if isinstance(s, StringSegmentValue)]
        overridables = [s for s in segments if isinstance(s, OverridableSegmentValue)]

        assert not any(s.path.endswith(".code") for s in string_segments)
        assert not any(SAMPLE_CODE.strip() in s.render_text() for s in string_segments)
        code_segments = [s for s in overridables if s.path.endswith(".code")]
        assert len(code_segments) == 1
        assert code_segments[0].data == SAMPLE_CODE
        assert code_segments[0].path.startswith("body.")
        assert any(s.path.endswith(".caption") and s.render_text() == "Greeting" for s in string_segments)

    def test_writer_round_trips_override(self, body_with_code):
        """The segments writer applies a code override to the right stream child."""
        locale, _ = Locale.objects.get_or_create(language_code="en")
        field = FeatherBasePage._meta.get_field("body")
        child = body_with_code[0]
        segments = [OverridableSegmentValue("code", "print('bonjour')").wrap(child.id)]

        StreamFieldSegmentsWriter(field, locale, locale).handle_stream_block(body_with_code, segments)

        assert body_with_code[0].value["code"] == "print('bonjour')"
        assert body_with_code[0].value["caption"] == "Greeting"
        assert body_with_code[0].value["language"] == "python"
